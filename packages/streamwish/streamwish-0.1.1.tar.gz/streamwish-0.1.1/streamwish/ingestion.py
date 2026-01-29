import os
from abc import ABC, abstractmethod
from typing import List, Generator, Any
# Lazy imports for optional dependencies to avoid errors if not installed immediately
# import pandas as pd
# from pypdf import PdfReader

class DataSource(ABC):
    @abstractmethod
    def stream_chunks(self) -> Generator[str, None, None]:
        """
        Yields text chunks from the source.
        """
        pass

class LocalFileSource(DataSource):
    def __init__(self, file_path: str):
        self.file_path = file_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

    def stream_chunks(self) -> Generator[str, None, None]:
        ext = os.path.splitext(self.file_path)[1].lower()
        
        if ext == '.txt' or ext == '.md':
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Naive chunking by line or paragraph. 
                # For StreamWish, let's treat each paragraph as a potential "event"
                # or read the whole file if small.
                content = f.read()
                # Simple split by double newline
                for chunk in content.split('\n\n'):
                    if chunk.strip():
                        yield chunk.strip()
                        
        elif ext == '.pdf':
            try:
                from pypdf import PdfReader
            except ImportError:
                yield "[Error: pypdf not installed]"
                return

            reader = PdfReader(self.file_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    yield text
                    
        elif ext in ['.xlsx', '.xls', '.csv']:
            try:
                import pandas as pd
            except ImportError:
                yield "[Error: pandas not installed]"
                return
                
            if ext == '.csv':
                df = pd.read_csv(self.file_path)
            else:
                df = pd.read_excel(self.file_path)
            
            # Convert each row to a string representation
            for _, row in df.iterrows():
                yield row.to_string()
                
        else:
            yield f"[Warning: Unsupported file type {ext}]"


class GoogleDriveSource(DataSource):
    def __init__(self, folder_id: str, credentials_path: str = None):
        """
        folder_id: The ID of the GDrive folder to stream from.
        credentials_path: Path to service account JSON (optional if using env vars).
        """
        self.folder_id = folder_id
        self.credentials_path = credentials_path
        
    def _authenticate(self):
        """
        Uses Google's Application Default Credentials (ADC).
        This supports:
        1. GOOGLE_APPLICATION_CREDENTIALS env var pointing to a Service Account JSON.
        2. GCloud CLI credentials (gcloud auth application-default login).
        3. Metadata server credentials (if running on GCP VM/Cloud Run).
        """
        try:
            import google.auth
            from googleapiclient.discovery import build
            
            # scopes for drive read-only
            SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
            
            creds, project = google.auth.default(scopes=SCOPES)
            self.service = build('drive', 'v3', credentials=creds)
            return True
        except ImportError:
            print("[Error] google-auth or google-api-python-client not installed.")
            return False
        except Exception as e:
            print(f"[Error] Authentication failed: {e}")
            return False

    def stream_chunks(self) -> Generator[str, None, None]:
        if not hasattr(self, 'service'):
            if not self._authenticate():
                yield "[Error: specific methods to authenticate failed]"
                return

        # List files in the folder
        try:
            results = self.service.files().list(
                q=f"'{self.folder_id}' in parents and trashed = false",
                pageSize=10,
                fields="nextPageToken, files(id, name, mimeType)"
            ).execute()
            items = results.get('files', [])

            if not items:
                yield "No files found in folder."
            else:
                for item in items:
                    # For now just yielding names, real impl would download content
                    yield f"Reading file: {item['name']} (ID: {item['id']})"
        except Exception as e:
            yield f"[Error querying Drive]: {e}"

class IngestionPipeline:
    def __init__(self):
        self.sources: List[DataSource] = []

    def add_source(self, source: DataSource):
        self.sources.append(source)

    def process(self) -> Generator[str, None, None]:
        for source in self.sources:
            yield from source.stream_chunks()
