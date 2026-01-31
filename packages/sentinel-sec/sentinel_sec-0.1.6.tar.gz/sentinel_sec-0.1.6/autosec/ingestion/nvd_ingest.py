import os
import gzip
import json
import logging
import requests
from typing import List, Dict, Any, Generator
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NVDIngester:
    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333, collection_name: str = "cve_data"):
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.collection_name = collection_name
        self.vector_size = 1536 # OpenAI embedding size, to be adjusted if using different model
        
        # Ensure collection exists
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            self.qdrant_client.get_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' exists.")
        except Exception:
            logger.info(f"Creating collection '{self.collection_name}'...")
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=self.vector_size, distance=models.Distance.COSINE),
            )

    def download_feed(self, year: str, output_dir: str = "data") -> str:
        """Downloads the NVD JSON 2.0 gz feed for a specific year."""
        url = f"https://nvd.nist.gov/feeds/json/cve/2.0/nvdcve-2.0-{year}.json.gz"
        os.makedirs(output_dir, exist_ok=True)
        filename = f"nvdcve-2.0-{year}.json.gz"
        filepath = os.path.join(output_dir, filename)
        
        logger.info(f"Downloading {url} to {filepath}...")
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info("Download complete.")
            return filepath
        else:
            raise Exception(f"Failed to download feed: {response.status_code}")

    def parse_gz(self, filepath: str) -> Generator[Dict[str, Any], None, None]:
        """Yields parsed CVEs from a gz file."""
        logger.info(f"Parsing {filepath}...")
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            data = json.load(f)
            vulnerabilities = data.get("vulnerabilities", [])
            for item in vulnerabilities:
                yield item.get("cve", {})

    def serialize_cve(self, cve: Dict[str, Any]) -> str:
        """Converts a CVE JSON object into a semantic narrative."""
        cve_id = cve.get("id", "Unknown ID")
        
        # English Description
        descriptions = cve.get("descriptions", [])
        desc_text = next((d["value"] for d in descriptions if d["lang"] == "en"), "No description available.")
        
        # CWE
        weaknesses = cve.get("weaknesses", [])
        cwe_ids = []
        for w in weaknesses:
            for desc in w.get("description", []):
                if desc.get("lang") == "en":
                    cwe_ids.append(desc.get("value"))
        cwe_str = ", ".join(cwe_ids) if cwe_ids else "unknown weakness"
        
        # CVSS
        metrics = cve.get("metrics", {})
        cvss_v31 = metrics.get("cvssMetricV31", [])
        if cvss_v31:
            data = cvss_v31[0].get("cvssData", {})
            score = data.get("baseScore", "N/A")
            vector = data.get("vectorString", "N/A")
            severity = cvss_v31[0].get("baseSeverity", "N/A")
            metrics_str = f"CVSS base score of {score} ({severity}), vector {vector}"
        else:
            metrics_str = "No CVSS V3.1 metrics"

        narrative = (
            f"{cve_id} is a vulnerability classified under {cwe_str}. "
            f"It is described as follows: {desc_text} "
            f"The vulnerability has a {metrics_str}."
        )
        return narrative

    # Placeholder for embedding - need to decide on model (OpenAI vs Local)
    def get_embedding(self, text: str) -> List[float]:
        # TODO: Implement OpenAI or local embedding call
        return [0.0] * self.vector_size

    def ingest_feed(self, year: str):
        filepath = self.download_feed(year)
        batch_points = []
        batch_size = 100
        
        for cve in self.parse_gz(filepath):
             narrative = self.serialize_cve(cve)
             embedding = self.get_embedding(narrative)
             
             payload = {
                 "cve_id": cve.get("id"),
                 "narrative": narrative,
                 "raw_json": json.dumps(cve)
             }
             
             # Using CVE ID hash or similar as point ID? 
             # Qdrant accepts string IDs (UUIDs) or integers. 
             # For simplicity, we can let Qdrant generate UUIDs or map CVE to UUID.
             # Here we accumulate points.
             
             # To keep it simple for this step, we will just print progress
             pass
        
        logger.info(f"Ingestion for {year} finished (Mocked).")

if __name__ == "__main__":
    ingester = NVDIngester()
    # For testing, we won't download the big file yet, or we'll mock it.
    print("Ingester initialized.")
