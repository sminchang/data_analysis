import pandas as pd
import re
from pathlib import Path


class ExcelProcessor:
    def __init__(self, folder_path: str):
        self.folder_path = Path(folder_path)
        self.excel_files = self._get_excel_files()
    
    def _get_excel_files(self) -> list:
        return list(self.folder_path.glob("*.xlsx")) + list(self.folder_path.glob("*.xls"))
    
    def _clean_filename(self, filename: str) -> str:
        name_without_ext = filename.stem
        keywords = ['.xlsx', '.hwp', '.pdf', '.hwpx', 'xlsx', 'hwp', 'pdf', 'hwpx']
        
        cleaned = name_without_ext
        for keyword in keywords:
            cleaned = re.sub(re.escape(keyword), '', cleaned, flags=re.IGNORECASE)
        
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        cleaned = re.sub(r'[_\-]+', ' ', cleaned).strip()
        
        return cleaned
    
    def union(self, output_filename: str = "union_result.xlsx") -> pd.DataFrame:
        """Vertical concatenation (UNION) - stack rows"""
        all_dfs = []
        
        for file_path in self.excel_files:
            try:
                df = pd.read_excel(file_path)
                df.insert(0, 'file_type', self._clean_filename(file_path))
                all_dfs.append(df)
            except Exception:
                continue
        
        if not all_dfs:
            raise ValueError("No valid files to process")
        
        result = pd.concat(all_dfs, axis=0, ignore_index=True, sort=False)
        result.to_excel(self.folder_path / output_filename, index=False)
        
        return result
    
    def join(self, output_filename: str = "join_result.xlsx") -> pd.DataFrame:
        """Horizontal concatenation (JOIN) - concatenate columns"""
        if not self.excel_files:
            raise ValueError("No Excel files found")
        
        # 첫 번째 파일은 헤더 포함하여 로드
        combined = pd.read_excel(self.excel_files[0])
        
        # 나머지 파일들은 헤더 제외하고 수평 결합
        for file_path in self.excel_files[1:]:
            try:
                df = pd.read_excel(file_path, skiprows=1)
                combined = pd.concat([combined, df], axis=1, ignore_index=False)
            except Exception:
                continue
        
        # 파일 유형 컬럼 추가
        cleaned_names = [self._clean_filename(f) for f in self.excel_files]
        num_rows = len(combined)
        
        if len(cleaned_names) <= num_rows:
            filename_col = cleaned_names + [''] * (num_rows - len(cleaned_names))
        else:
            filename_col = cleaned_names[:num_rows]
        
        combined = combined.reset_index(drop=True)
        combined.insert(0, 'file_type', filename_col)
        
        combined.to_excel(self.folder_path / output_filename, index=False)
        
        return combined
    
    def merge_sheets(self, output_filename: str = "merged_sheets.xlsx") -> None:
        """각 파일을 한 파일의 별도 시트로 통합"""
        if not self.excel_files:
            raise ValueError("No Excel files found")
        
        with pd.ExcelWriter(self.folder_path / output_filename, engine='openpyxl') as writer:
            for file_path in self.excel_files:
                try:
                    df = pd.read_excel(file_path)
                    sheet_name = self._clean_filename(file_path)
                    
                    # 시트명 길이 제한 (31자) 및 특수문자 제거
                    sheet_name = re.sub(r'[\\/*?:"<>|]', '', sheet_name)[:31]
                    if not sheet_name:
                        sheet_name = f"Sheet_{self.excel_files.index(file_path) + 1}"
                    
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                except Exception:
                    continue


if __name__ == "__main__":
    folder_path = r"C:\Users\yunis\Desktop\Gemini2.0_ouput_v3"  # Change this path
    
    processor = ExcelProcessor(folder_path)
    
    # Choose one:
    # result = processor.union("union_output.xlsx")        # 수직결합
    # result = processor.join("join_output.xlsx")          # 수평결합
    processor.merge_sheets("multi_sheet_output.xlsx")     # 다중시트 통합