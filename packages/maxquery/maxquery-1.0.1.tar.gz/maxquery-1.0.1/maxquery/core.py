"""Core MaxQuery query execution logic"""
import sys
from pathlib import Path
from typing import List, Dict, Optional
from odps import ODPS
import pandas as pd
from maxquery.credentials import CredentialsManager


class MaxQueryRunner:
    """Execute SQL queries on MaxCompute (ODPS)"""
    
    OUTPUT_FORMATS = {
        '1': {'name': 'CSV', 'extension': '.csv'},
        '2': {'name': 'Parquet', 'extension': '.parquet'}
    }
    
    def __init__(self, output_dir: str = "outputs"):
        """Initialize MaxQuery runner
        
        Args:
            output_dir: Directory to save query results
        """
        self.output_dir = Path(output_dir)
        self.odps = None
    
    def connect(self) -> bool:
        """Connect to MaxCompute using credentials
        
        Returns:
            bool: True if successful, False otherwise
        """
        credentials = CredentialsManager.get_credentials()
        
        if not credentials or not all(credentials.values()):
            print("❌ Error: Missing MaxCompute credentials")
            print("   Run: maxquery config --setup")
            return False
        
        try:
            self.odps = ODPS(
                credentials['access_id'],
                credentials['access_key'],
                credentials['project'],
                credentials.get('endpoint', 'http://service.odps.aliyun.com/api')
            )
            print(f"✅ Connected to ODPS Project: {credentials['project']}")
            return True
        except Exception as e:
            print(f"❌ Connection error: {str(e)}")
            return False
    
    def run_query(
        self,
        sql_file: str,
        output_format: str = '1',
        download: bool = True
    ) -> Dict:
        """Execute a single SQL file
        
        Args:
            sql_file: Path to SQL file
            output_format: '1' for CSV, '2' for Parquet
            download: Whether to save results to disk
        
        Returns:
            dict: Query execution result
        """
        sql_path = Path(sql_file)
        
        if not sql_path.exists():
            print(f"❌ File not found: {sql_file}")
            return {'status': 'error', 'file': sql_file, 'error': 'File not found'}
        
        # Read SQL
        with open(sql_path, 'r') as f:
            query = f.read().strip()
        
        if not query:
            return {'status': 'skipped', 'file': sql_file, 'reason': 'Empty file'}
        
        file_name = sql_path.stem
        print(f"\n📄 {file_name}...")
        
        try:
            # Execute query
            result = self.odps.execute_sql(query)
            df = result.open_reader().to_pandas()
            
            # Download to local files if requested
            if download:
                self.output_dir.mkdir(exist_ok=True)
                
                fmt = self.OUTPUT_FORMATS.get(output_format, self.OUTPUT_FORMATS['1'])
                output_file = self.output_dir / f"{file_name}{fmt['extension']}"
                
                if fmt['name'] == 'Parquet':
                    df.to_parquet(output_file, index=False)
                else:
                    df.to_csv(output_file, index=False)
                
                print(f"   ✅ {len(df)} records → {output_file}")
                output_path = str(output_file)
            else:
                print(f"   ✅ {len(df)} records (in-memory)")
                output_path = "in-memory"
            
            return {
                'status': 'success',
                'file': file_name,
                'records': len(df),
                'output': output_path
            }
            
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"   ❌ Error: {error_msg}")
            return {'status': 'error', 'file': file_name, 'error': error_msg}
    
    def run_queries(
        self,
        sql_files: List[str],
        output_format: str = '1',
        download: bool = True
    ) -> None:
        """Execute multiple SQL files
        
        Args:
            sql_files: List of SQL file paths
            output_format: '1' for CSV, '2' for Parquet
            download: Whether to save results to disk
        """
        if not sql_files:
            print("❌ No SQL files specified")
            return
        
        print(f"\n📊 Running {len(sql_files)} query(ies)")
        fmt_name = self.OUTPUT_FORMATS.get(output_format, self.OUTPUT_FORMATS['1'])['name']
        print(f"   Format: {fmt_name}")
        print("="*60)
        
        if not self.connect():
            sys.exit(1)
        
        # Execute each file
        results = []
        for sql_file in sql_files:
            result = self.run_query(sql_file, output_format, download)
            results.append(result)
        
        # Summary
        successful = [r for r in results if r['status'] == 'success']
        print("\n" + "="*60)
        print(f"✅ Completed: {len(successful)}/{len(sql_files)} queries")
        total_records = sum(r.get('records', 0) for r in successful)
        print(f"📊 Total records: {total_records}")
        if download:
            print(f"💾 Results saved to: {self.output_dir}")
        else:
            print(f"💾 Results kept in memory (not downloaded)")
