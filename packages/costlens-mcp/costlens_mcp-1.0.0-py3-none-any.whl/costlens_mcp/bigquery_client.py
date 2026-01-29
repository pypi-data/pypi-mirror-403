"""BigQuery client for fetching table metadata and executing queries with cost awareness."""

from typing import Optional, Any
from dataclasses import dataclass
from .schemas import TableInfo


@dataclass
class DryRunResult:
    """Result of a dry-run query."""
    total_bytes_processed: int
    total_bytes_human: str
    estimated_cost_usd: float
    is_valid: bool
    error_message: Optional[str] = None


@dataclass
class QueryResult:
    """Result of an executed query."""
    rows: list[dict[str, Any]]
    total_rows: int
    bytes_processed: int
    cost_usd: float


class BigQueryClient:
    """Client for interacting with BigQuery API with FinOps capabilities.
    
    Supports:
    1. Service Account key file (--key-file)
    2. Application Default Credentials (gcloud auth application-default login)
    3. Default compute credentials (on GCP VMs)
    """
    
    PRICE_PER_TB = 5.0  # $5 per TB scanned
    
    def __init__(
        self, 
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        key_file: Optional[str] = None
    ):
        self.project_id = project_id
        self.location = location or "US"
        self.key_file = key_file
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of BigQuery client with ADC support."""
        if self._client is None:
            try:
                from google.cloud import bigquery
                
                credentials = None
                
                # Priority 1: Explicit service account key file
                if self.key_file:
                    from google.oauth2 import service_account
                    credentials = service_account.Credentials.from_service_account_file(
                        self.key_file,
                        scopes=["https://www.googleapis.com/auth/cloud-platform"],
                    )
                # Priority 2 & 3: ADC or compute credentials (handled automatically)
                
                self._client = bigquery.Client(
                    credentials=credentials,
                    project=self.project_id,
                    location=self.location
                )
            except Exception as e:
                raise RuntimeError(f"Failed to initialize BigQuery client: {e}")
        return self._client
    
    def dry_run_query(self, sql: str) -> DryRunResult:
        """Perform a dry-run to estimate query cost without executing."""
        try:
            from google.cloud import bigquery
            
            client = self._get_client()
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            
            query_job = client.query(sql, job_config=job_config)
            
            bytes_processed = query_job.total_bytes_processed or 0
            cost_usd = (bytes_processed / (1024**4)) * self.PRICE_PER_TB
            
            return DryRunResult(
                total_bytes_processed=bytes_processed,
                total_bytes_human=self._format_bytes(bytes_processed),
                estimated_cost_usd=round(cost_usd, 6),
                is_valid=True
            )
        except Exception as e:
            return DryRunResult(
                total_bytes_processed=0,
                total_bytes_human="0 B",
                estimated_cost_usd=0,
                is_valid=False,
                error_message=str(e)
            )
    
    def execute_query(
        self, 
        sql: str, 
        max_cost_usd: Optional[float] = None,
        force: bool = False
    ) -> QueryResult:
        """Execute a query with optional cost gate."""
        if not force:
            dry_run = self.dry_run_query(sql)
            
            if not dry_run.is_valid:
                raise ValueError(f"Query validation failed: {dry_run.error_message}")
            
            if max_cost_usd and dry_run.estimated_cost_usd > max_cost_usd:
                raise ValueError(
                    f"Query cost ${dry_run.estimated_cost_usd:.4f} exceeds limit ${max_cost_usd:.4f}. "
                    f"Would scan {dry_run.total_bytes_human}."
                )
        
        client = self._get_client()
        query_job = client.query(sql)
        results = query_job.result()
        
        rows = [dict(row.items()) for row in results]
        bytes_processed = query_job.total_bytes_processed or 0
        cost_usd = (bytes_processed / (1024**4)) * self.PRICE_PER_TB
        
        return QueryResult(
            rows=rows,
            total_rows=len(rows),
            bytes_processed=bytes_processed,
            cost_usd=round(cost_usd, 6)
        )
    
    def list_tables(self, dataset_filter: Optional[list[str]] = None) -> list[dict]:
        """List all tables with size information."""
        client = self._get_client()
        
        if dataset_filter:
            datasets = [client.dataset(d) for d in dataset_filter]
        else:
            datasets = list(client.list_datasets())
        
        tables = []
        for dataset in datasets:
            dataset_id = dataset.dataset_id
            for table_ref in client.list_tables(dataset_id):
                try:
                    table = client.get_table(table_ref)
                    tables.append({
                        "name": f"{dataset_id}.{table.table_id}",
                        "full_name": f"{self.project_id}.{dataset_id}.{table.table_id}",
                        "size_bytes": table.num_bytes or 0,
                        "size_human": self._format_bytes(table.num_bytes or 0),
                        "num_rows": table.num_rows or 0,
                        "is_partitioned": table.time_partitioning is not None,
                        "partition_column": (
                            table.time_partitioning.field 
                            if table.time_partitioning else None
                        ),
                        "is_clustered": bool(table.clustering_fields),
                    })
                except Exception:
                    tables.append({
                        "name": f"{dataset_id}.{table_ref.table_id}",
                        "error": "Access denied or table not found"
                    })
        
        return tables
    
    def describe_table(self, table_name: str) -> dict:
        """Get detailed schema and metadata for a table."""
        client = self._get_client()
        table = client.get_table(table_name)
        
        return {
            "name": table.table_id,
            "full_name": f"{table.project}.{table.dataset_id}.{table.table_id}",
            "description": table.description,
            "num_rows": table.num_rows,
            "size_bytes": table.num_bytes,
            "size_human": self._format_bytes(table.num_bytes or 0),
            "schema": [
                {
                    "name": field.name,
                    "type": field.field_type,
                    "mode": field.mode,
                }
                for field in table.schema
            ],
            "partitioning": {
                "type": table.time_partitioning.type_ if table.time_partitioning else None,
                "field": table.time_partitioning.field if table.time_partitioning else None,
            } if table.time_partitioning else None,
            "clustering": list(table.clustering_fields) if table.clustering_fields else None,
        }
    
    def get_table_info(self, full_table_name: str) -> Optional[TableInfo]:
        """Fetch metadata for a specific table."""
        try:
            client = self._get_client()
            table = client.get_table(full_table_name)
            
            is_partitioned = table.time_partitioning is not None
            partition_column = None
            partition_type = None
            
            if table.time_partitioning:
                partition_column = table.time_partitioning.field or "_PARTITIONTIME"
                partition_type = table.time_partitioning.type_
            
            cluster_columns = list(table.clustering_fields) if table.clustering_fields else []
            
            return TableInfo(
                name=table.table_id,
                full_name=full_table_name,
                num_rows=table.num_rows,
                size_bytes=table.num_bytes,
                size_human=self._format_bytes(table.num_bytes) if table.num_bytes else None,
                columns_total=len(table.schema) if table.schema else 0,
                is_partitioned=is_partitioned,
                partition_column=partition_column,
                partition_type=partition_type,
                is_clustered=len(cluster_columns) > 0,
                cluster_columns=cluster_columns,
            )
        except Exception as e:
            print(f"Warning: Could not fetch metadata for {full_table_name}: {e}")
            return None
    
    def _format_bytes(self, bytes_count: int) -> str:
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        unit_index = 0
        size = float(bytes_count)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        return f"{size:.2f} {units[unit_index]}"


class MockBigQueryClient:
    """Mock client for approximate estimations (no GCP connection)."""
    
    DEFAULT_SIZES = {
        "users": 100 * 1024 * 1024,
        "events": 10 * 1024**3,
        "logs": 50 * 1024**3,
        "transactions": 5 * 1024**3,
    }
    
    def dry_run_query(self, sql: str) -> DryRunResult:
        estimated_bytes = 1 * 1024**3  # 1 GB default
        cost_usd = (estimated_bytes / (1024**4)) * 5.0
        
        return DryRunResult(
            total_bytes_processed=estimated_bytes,
            total_bytes_human="~1 GB (simulated)",
            estimated_cost_usd=round(cost_usd, 6),
            is_valid=True,
            error_message="Using simulated estimation - connect to BigQuery for precise costs"
        )
    
    def execute_query(self, sql: str, **kwargs) -> QueryResult:
        raise ValueError("Cannot execute queries in simulation mode. Provide --project.")
    
    def list_tables(self, **kwargs) -> list[dict]:
        return [{"error": "Connect to BigQuery to list tables (--project)"}]
    
    def describe_table(self, table_name: str) -> dict:
        return {"error": f"Connect to BigQuery to describe {table_name}"}
    
    def get_table_info(self, full_table_name: str) -> TableInfo:
        parts = full_table_name.split(".")
        table_name = parts[-1].lower() if parts else "unknown"
        size_bytes = self.DEFAULT_SIZES.get(table_name, 1 * 1024**3)
        
        return TableInfo(
            name=table_name,
            full_name=full_table_name,
            num_rows=None,
            size_bytes=size_bytes,
            size_human=f"{size_bytes / (1024**3):.2f} GB",
            columns_total=50,
            is_partitioned=False,
        )


def get_bigquery_client(
    project_id: Optional[str] = None,
    location: Optional[str] = None,
    key_file: Optional[str] = None
) -> BigQueryClient | MockBigQueryClient:
    """Get BigQuery client, falling back to mock if no credentials."""
    if project_id:
        try:
            client = BigQueryClient(project_id, location, key_file)
            client._get_client()  # Test connection
            return client
        except Exception:
            pass
    return MockBigQueryClient()
