"""
pdfplumber의 extract_table()을 개선한 테이블 추출 기능 제공
- 텍스트 레이어가 아닌 화면에 보이는 페이지 내용을 기반으로 테이블 추출
- 점선 테이블 인식
- 외곽선이 없는 테이블 인식
"""

import os
import cv2
import numpy as np
import pandas as pd
import pdfplumber


class TableExtractorConfig:
    """테이블 추출 설정 클래스"""
    
    # 이미지 처리를 위한 상수
    RESOLUTION = 150  # 이미지 해상도
    LINE_WIDTH = 1  # 선 두께
    MERGE_THRESHOLD = 3  # 좌표 병합 임계값 (픽셀)
    HOUGH_THRESHOLD = 12  # 허프 변환 임계값
    MIN_LINE_LENGTH = 5  # 최소 선 길이
    MAX_LINE_GAP = 6  # 최대 선 간격
    ANGLE_HORIZONTAL_THRESHOLD = 5  # 수평선 각도 임계값
    ANGLE_VERTICAL_THRESHOLD = 85  # 수직선 각도 임계값
    CELL_OVERLAP_THRESHOLD = 0.1  # 셀 중첩 임계값 (10%)
    
    def __init__(self, **kwargs):
        """
        설정 초기화
        
        Args:
            **kwargs: 설정 오버라이드를 위한 키워드 인자
        """
        # 기본 설정값 복사
        self.resolution = self.RESOLUTION
        self.line_width = self.LINE_WIDTH
        self.merge_threshold = self.MERGE_THRESHOLD
        self.hough_threshold = self.HOUGH_THRESHOLD
        self.min_line_length = self.MIN_LINE_LENGTH
        self.max_line_gap = self.MAX_LINE_GAP
        self.angle_horizontal_threshold = self.ANGLE_HORIZONTAL_THRESHOLD
        self.angle_vertical_threshold = self.ANGLE_VERTICAL_THRESHOLD
        self.cell_overlap_threshold = self.CELL_OVERLAP_THRESHOLD
        
        # 사용자 지정 설정 적용
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


class GeometryUtils:
    """기하학적 연산 및 좌표 처리 유틸리티 클래스"""
    
    @staticmethod
    def merge_coords(coords, threshold):
        """
        가까운 좌표를 병합하여 노이즈를 제거하는 함수
        
        Args:
            coords: 병합할 좌표 목록
            threshold: 병합 임계값 (픽셀)
            
        Returns:
            병합된 좌표 목록
        """
        if not coords:
            return []
            
        # 좌표 정렬
        coords = sorted(coords)
        
        merged = []
        current_group = [coords[0]]

        for coord in coords[1:]:
            if coord - current_group[-1] <= threshold:
                current_group.append(coord)
            else:
                merged.append(sum(current_group) / len(current_group))
                current_group = [coord]

        if current_group:
            merged.append(sum(current_group) / len(current_group))

        return merged


class LineDetector:
    """테이블 선 감지 및 처리 클래스"""
    
    def __init__(self, config):
        """
        LineDetector 초기화
        
        Args:
            config: TableExtractorConfig 인스턴스
        """
        self.config = config
    
    def extract_lines_from_mask(self, table_mask, table_id=None, debug_dir=None):
        """
        테이블 마스크에서 수평선과 수직선을 추출하는 함수
        
        Args:
            table_mask: 테이블 영역의 이진 마스크
            img: 디버깅용 시각화 이미지 (선택 사항)

        Returns:
            (수평선 목록, 수직선 목록) 튜플
            수평선 형식: (y, x0, x1)
            수직선 형식: (x, y0, y1)
        """
        # 선 감지를 위한 전처리
        lines_img = table_mask.copy()
        _, binary = cv2.threshold(lines_img, 127, 255, cv2.THRESH_BINARY)

        # 허프 변환으로 선 감지
        lines = cv2.HoughLinesP(
            binary, 
            1, 
            np.pi / 180,
            threshold=self.config.hough_threshold,
            minLineLength=self.config.min_line_length,
            maxLineGap=self.config.max_line_gap
        )

        # 디버깅용 시각화
        if lines is not None and debug_dir and table_id:
            debug_img = cv2.cvtColor(table_mask.copy(), cv2.COLOR_GRAY2BGR)
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(debug_img, (x1, y1), (x2, y2), (0, 0, 255), 1)
            cv2.imwrite(os.path.join(debug_dir, f"step3_{table_id}_hough_lines.png"), debug_img)

        # 선 분리
        h_lines = []  # 수평선: (y, x0, x1)
        v_lines = []  # 수직선: (x, y0, y1)

        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                # 선의 각도 계산
                angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
                
                # 수평선 (각도가 0 또는 180에 가까움)
                if angle < self.config.angle_horizontal_threshold or angle > (180 - self.config.angle_horizontal_threshold):
                    h_lines.append((min(y1, y2), min(x1, x2), max(x1, x2)))
                
                # 수직선 (각도가 90에 가까움)
                elif (90 - self.config.angle_vertical_threshold) < angle < (90 + self.config.angle_vertical_threshold):
                    v_lines.append((min(x1, x2), min(y1, y2), max(y1, y2)))
        
        # 좌표에 따라 정렬
        h_lines.sort()  # y 좌표 기준 정렬
        v_lines.sort()  # x 좌표 기준 정렬
        
        return h_lines, v_lines
    
    def add_table_boundary(self, h_lines, v_lines, x, y, w, h):
        """
        테이블 외곽 경계를 실제 선 정보로 추가하는 함수
        
        Args:
            h_lines: 수평선 목록
            v_lines: 수직선 목록
            x: 테이블 왼쪽 상단 x 좌표
            y: 테이블 왼쪽 상단 y 좌표
            w: 테이블 너비
            h: 테이블 높이
            
        Returns:
            (업데이트된 수평선 목록, 업데이트된 수직선 목록) 튜플
        """
        # 테이블 외곽 좌표
        left = x
        right = x + w
        top = y
        bottom = y + h
        
        # 수평선 경계 추가 (상단, 하단)
        top_border = (top, left, right)  # (y, x0, x1) 형식
        bottom_border = (bottom, left, right)
        
        # 수직선 경계 추가 (좌측, 우측)
        left_border = (left, top, bottom)  # (x, y0, y1) 형식
        right_border = (right, top, bottom)
        
        # 기존 선 목록에 외곽 경계 추가
        updated_h_lines = list(h_lines) if h_lines is not None else []
        updated_v_lines = list(v_lines) if v_lines is not None else []
        
        # 이미 유사한 선이 있는지 확인 후 추가
        if not any(abs(line[0] - top) < 5 and abs(line[1] - left) < 5 and abs(line[2] - right) < 5 for line in updated_h_lines):
            updated_h_lines.append(top_border)
        
        if not any(abs(line[0] - bottom) < 5 and abs(line[1] - left) < 5 and abs(line[2] - right) < 5 for line in updated_h_lines):
            updated_h_lines.append(bottom_border)
        
        if not any(abs(line[0] - left) < 5 and abs(line[1] - top) < 5 and abs(line[2] - bottom) < 5 for line in updated_v_lines):
            updated_v_lines.append(left_border)
        
        if not any(abs(line[0] - right) < 5 and abs(line[1] - top) < 5 and abs(line[2] - bottom) < 5 for line in updated_v_lines):
            updated_v_lines.append(right_border)
        
        return updated_h_lines, updated_v_lines


class GridManager:
    """테이블 그리드 생성 및 관리 클래스"""
    
    def __init__(self, config):
        """
        GridManager 초기화
        
        Args:
            config: TableExtractorConfig 인스턴스
        """
        self.config = config
    
    def create_grid_lines(self, h_y_coords, v_x_coords):
        """
        그리드 좌표로부터 그리드 라인 생성
        
        Args:
            h_y_coords: 수평선 y 좌표 목록
            v_x_coords: 수직선 x 좌표 목록
            
        Returns:
            (그리드 수평선 목록, 그리드 수직선 목록) 튜플
        """
        grid_h_lines = []  # 그리드 수평선: (y, x_min, x_max)
        grid_v_lines = []  # 그리드 수직선: (x, y_min, y_max)
        
        # x_min, x_max, y_min, y_max 계산
        x_min = min(v_x_coords) if v_x_coords else 0
        x_max = max(v_x_coords) if v_x_coords else 1000
        y_min = min(h_y_coords) if h_y_coords else 0
        y_max = max(h_y_coords) if h_y_coords else 1000
        
        # 그리드 수평선 생성
        for y in h_y_coords:
            grid_h_lines.append((y, x_min, x_max))
        
        # 그리드 수직선 생성
        for x in v_x_coords:
            grid_v_lines.append((x, y_min, y_max))
        
        return grid_h_lines, grid_v_lines


class MergedCellDetector:
    """병합된 셀 감지 및 처리 클래스"""
    
    def __init__(self, config):
        """
        MergedCellDetector 초기화
        
        Args:
            config: TableExtractorConfig 인스턴스
        """
        self.config = config

    def detect_merged_cells(self, h_lines, v_lines, grid_h_lines, grid_v_lines, h_y_coords, v_x_coords):
        """
        실제 선과 그리드 선을 비교하여 병합셀 감지
        
        Args:
            h_lines: 감지된 실제 수평선 (y, x0, x1) 형식
            v_lines: 감지된 실제 수직선 (x, y0, y1) 형식
            grid_h_lines: 생성된 그리드 수평선 (y, x_min, x_max) 형식
            grid_v_lines: 생성된 그리드 수직선 (x, y_min, y_max) 형식
            h_y_coords: 병합된 수평선 y좌표 목록
            v_x_coords: 병합된 수직선 x좌표 목록

        Returns:
            병합 그룹 목록 [(min_row, min_col, max_row, max_col), ...]
        """
        # 그리드 선과 실제 선 비교를 위한 임계값
        threshold = self.config.merge_threshold
        
        # 행과 열의 수 계산
        rows = len(h_y_coords) - 1
        cols = len(v_x_coords) - 1
        
        # 셀별 병합 상태를 저장할 매트릭스 초기화
        # 0: 병합되지 않음, 1: 아래쪽과 병합(행 병합), 2: 오른쪽과 병합(열 병합), 3: 아래쪽 및 오른쪽과 병합
        merged_matrix = np.zeros((rows, cols), dtype=int)
        
        # 각 수평 그리드 라인에 대해 실제 수평선의 세그먼트들 저장
        h_line_segments = {}  # key: grid_y 값, value: (x0, x1) 세그먼트 목록
        for grid_y, grid_x0, grid_x1 in grid_h_lines:
            h_line_segments[grid_y] = []
            # 이 그리드 라인과 일치하는 실제 선 찾기
            for y, x0, x1 in h_lines:
                if abs(y - grid_y) <= threshold:
                    h_line_segments[grid_y].append((x0, x1))

        # 각 수직 그리드 라인에 대해 실제 수직선의 세그먼트들 저장
        v_line_segments = {}  # key: grid_x 값, value: (y0, y1) 세그먼트 목록
        for grid_x, grid_y0, grid_y1 in grid_v_lines:
            v_line_segments[grid_x] = []
            # 이 그리드 라인과 일치하는 실제 선 찾기
            for x, y0, y1 in v_lines:
                if abs(x - grid_x) <= threshold:
                    v_line_segments[grid_x].append((y0, y1))

        # 각 셀의 경계선 유무 확인
        for i in range(rows):
            for j in range(cols):

                top_y = h_y_coords[i]
                bottom_y = h_y_coords[i + 1]
                left_x = v_x_coords[j]
                right_x = v_x_coords[j + 1]
                
                # 아래쪽 경계선 확인 (행 병합 감지)
                if i < rows - 1:  # 마지막 행이 아닌 경우만
                    bottom_border_exists = False
                    grid_y = h_y_coords[i + 1]
                    
                    # 그리드 라인에 대응하는 실제 선 세그먼트 확인
                    if grid_y in h_line_segments:
                        for x0, x1 in h_line_segments[grid_y]:
                            # 세그먼트가 셀의 x 범위와 충분히 겹치는지 확인
                            if not (x1 < left_x + threshold or x0 > right_x - threshold):
                                # 세그먼트가 셀 너비의 적어도 10% 이상 커버하는지
                                if min(x1, right_x) - max(x0, left_x) >= (right_x - left_x) * self.config.cell_overlap_threshold:
                                    bottom_border_exists = True
                                    break
                    
                    if not bottom_border_exists:
                        merged_matrix[i, j] = 1  # 아래쪽과 병합
                
                # 오른쪽 경계선 확인 (열 병합 감지)
                if j < cols - 1:  # 마지막 열이 아닌 경우만
                    right_border_exists = False
                    grid_x = v_x_coords[j + 1]
                    
                    # 그리드 라인에 대응하는 실제 선 세그먼트 확인
                    if grid_x in v_line_segments:
                        for y0, y1 in v_line_segments[grid_x]:
                            # 세그먼트가 셀의 y 범위와 충분히 겹치는지 확인
                            if not (y1 < top_y + threshold or y0 > bottom_y - threshold):
                                # 세그먼트가 셀 높이의 적어도 10% 이상 커버하는지
                                if min(y1, bottom_y) - max(y0, top_y) >= (bottom_y - top_y) * self.config.cell_overlap_threshold:
                                    right_border_exists = True
                                    break
                    
                    if not right_border_exists:
                        if merged_matrix[i, j] == 0:
                            merged_matrix[i, j] = 2  # 오른쪽과 병합
                        else:
                            merged_matrix[i, j] = 3  # 아래쪽 및 오른쪽과 병합
        
        # 병합 그룹 생성
        merged_groups = []
        visited = np.zeros((rows, cols), dtype=bool)
        
        for i in range(rows):
            for j in range(cols):
                if visited[i, j]:
                    continue
                
                # 병합되지 않은 셀은 건너뛰기
                if merged_matrix[i, j] == 0:
                    visited[i, j] = True
                    continue
                
                # 병합 그룹 시작
                group = [(i, j)]
                visited[i, j] = True
                
                # 병합 그룹의 경계
                min_row, max_row = i, i
                min_col, max_col = j, j
                
                # 그룹에 속한 모든 셀 찾기
                queue = [(i, j)]
                while queue:
                    r, c = queue.pop(0)
                    
                    # 아래쪽과 병합된 경우 (값 1 또는 값 3)
                    if r < rows - 1 and (merged_matrix[r, c] == 1 or merged_matrix[r, c] == 3) and not visited[r + 1, c]:
                        visited[r + 1, c] = True
                        group.append((r + 1, c))
                        queue.append((r + 1, c))
                        max_row = max(max_row, r + 1)
                    
                    # 오른쪽과 병합된 경우 (값 2 또는 값 3)
                    if c < cols - 1 and (merged_matrix[r, c] == 2 or merged_matrix[r, c] == 3) and not visited[r, c + 1]:
                        visited[r, c + 1] = True
                        group.append((r, c + 1))
                        queue.append((r, c + 1))
                        max_col = max(max_col, c + 1)
                
                # 병합 그룹 정보 저장
                if len(group) > 1:
                    merged_groups.append((min_row, min_col, max_row, max_col))

        return merged_groups


class TableDataExtractor:
    """테이블 데이터 추출 클래스"""
    
    def __init__(self, config):
        """
        TableDataExtractor 초기화
        
        Args:
            config: TableExtractorConfig 인스턴스
        """
        self.config = config
        self.line_detector = LineDetector(config)
        self.grid_manager = GridManager(config)
        self.merged_cell_detector = MergedCellDetector(config)
        self.geometry_utils = GeometryUtils()
    
    def extract_table_data(self, table_info, lined_cv, page, h_lines=None, v_lines=None, debug_dir=None, file_name="file_name"):
        """
        개별 테이블 영역에서 데이터 추출 (특정 셀 단위 병합셀 처리)
        
        Args:
            table_info: 테이블 정보 딕셔너리 {'id': int, 'mask': np.ndarray, 'bbox': tuple}
            lined_cv: 라인이 그려진 페이지 이미지
            page: pdfplumber 페이지 객체
            h_lines: 수평선 목록 (선택 사항)
            v_lines: 수직선 목록 (선택 사항)
            debug_dir: 디버깅 이미지 저장 디렉토리 (선택 사항)
            file_name: 파일 이름 (디버깅용)
            
        Returns:
            테이블 데이터 또는 None (실패 시)
        """
        table_id = table_info['id']
        table_mask = table_info['mask']
        x, y, x_end, y_end = table_info['bbox']

        # 선 추출이 제공되지 않은 경우에만 새로 추출
        if h_lines is None or v_lines is None:
            # 테이블 영역 내의 선 추출
            h_lines, v_lines = self.line_detector.extract_lines_from_mask(table_mask, table_id, debug_dir)
            
            # 테이블 외곽 경계 추가
            h_lines, v_lines = self.line_detector.add_table_boundary(
                h_lines, v_lines, 0, 0, table_mask.shape[1], table_mask.shape[0])

        # 추출된 선 정보로부터 좌표 추출
        h_y_coords = sorted(set([line[0] for line in h_lines]))
        v_x_coords = sorted(set([line[0] for line in v_lines]))

        # 가까운 좌표 병합(좌표 노이즈 제거)
        h_y_coords = self.geometry_utils.merge_coords(h_y_coords, self.config.merge_threshold)
        v_x_coords = self.geometry_utils.merge_coords(v_x_coords, self.config.merge_threshold)

        # 테이블 구조 유효성 검사
        rows = len(h_y_coords) - 1
        cols = len(v_x_coords) - 1

        if rows <= 0 or cols <= 0:
            return None
        
        # 그리드 라인 생성
        grid_h_lines, grid_v_lines = self.grid_manager.create_grid_lines(h_y_coords, v_x_coords)
        
        # 병합셀 감지 (특정 셀 단위)
        merged_cells = self.merged_cell_detector.detect_merged_cells(
            h_lines, v_lines, grid_h_lines, grid_v_lines, h_y_coords, v_x_coords)
        
        # 이미지 해상도에 맞게 좌표 변환 (이미지 좌표 → PDF 좌표)
        resolution_ratio = page.height / lined_cv.shape[0]
        h_y_coords_pdf = [y_coord * resolution_ratio for y_coord in h_y_coords]
        v_x_coords_pdf = [x_coord * resolution_ratio for x_coord in v_x_coords]

        # 테이블 데이터 추출
        table_data = [['' for _ in range(cols)] for _ in range(rows)]

        padding = 5 * resolution_ratio

        # 병합셀 처리를 위한 변수
        processed_cells = set()
        
        # 병합 그룹별 데이터 추출
        for min_row, min_col, max_row, max_col in merged_cells:
            y0 = h_y_coords_pdf[min_row]
            y1 = h_y_coords_pdf[max_row + 1]
            x0 = v_x_coords_pdf[min_col]
            x1 = v_x_coords_pdf[max_col + 1]

            # 모아찍기 해제로 x 좌표값이 페이지 범위를 벗어난 경우 조정
            if x0 < page.bbox[0] and x1 < page.bbox[0]:
                x0 += page.width
                x1 += page.width
            
            # 패딩 추가하여 셀 내용 추출
            cell_bbox = (x0 + padding, y0 + padding, x1 - padding, y1 - padding)
            if cell_bbox[2] <= cell_bbox[0] or cell_bbox[3] <= cell_bbox[1]:
                cell_bbox = (x0, y0, x1, y1)
            
            try:
                cell_text = page.crop(cell_bbox).extract_text() or ''
                cell_text = cell_text.strip()
                
                # 병합 그룹의 대표 셀(좌상단)에 데이터 배치
                table_data[min_row][min_col] = cell_text
                
                # 그룹의 모든 셀을 처리 완료로 표시
                for row in range(min_row, max_row + 1):
                    for col in range(min_col, max_col + 1):
                        processed_cells.add((row, col))

                        # 대표 셀(좌상단)이 아닌 병합셀 영역은 None으로 설정
                        if (row != min_row or col != min_col):
                            table_data[row][col] = None

            except Exception as e:
                print(f"{file_name} 병합셀 추출 오류 ({min_row}-{max_row}, {min_col}-{max_col}): {e}")
        
        # 일반 셀 데이터 추출
        for i in range(rows):
            for j in range(cols):
                # 이미 처리된 셀은 건너뛰기
                if (i, j) in processed_cells:
                    continue
                
                y0 = h_y_coords_pdf[i]
                y1 = h_y_coords_pdf[i + 1]
                x0 = v_x_coords_pdf[j]
                x1 = v_x_coords_pdf[j + 1]

                # 모아찍기 해제로 x 좌표값이 페이지 범위를 벗어난 경우 조정
                if x0 < page.bbox[0] and x1 < page.bbox[0]:
                    x0 += page.width
                    x1 += page.width
                
                # 패딩 추가하여 셀 내용 추출
                cell_bbox = (x0 + padding, y0 + padding, x1 - padding, y1 - padding)
                if cell_bbox[2] <= cell_bbox[0] or cell_bbox[3] <= cell_bbox[1]:
                    cell_bbox = (x0, y0, x1, y1)
                
                try:
                    cell_text = page.crop(cell_bbox).extract_text() or ''
                    table_data[i][j] = cell_text.strip()
                except Exception as e:
                    print(f"{file_name}셀 추출 오류 ({i}, {j}): {e}")
        
        # 디버깅 시각화를 위한 정보도 함께 반환
        if debug_dir:
            return table_data, merged_cells, h_y_coords, v_x_coords, y, x
        else:
            return table_data, merged_cells, None, None, None, None


class TableExtractor:
    """PDF에서 테이블을 추출하는 메인 클래스"""
    
    def __init__(self, config=None):
        """
        TableExtractor 초기화
        
        Args:
            config: TableExtractorConfig 인스턴스 (선택 사항)
        """
        self.config = config or TableExtractorConfig()
        self.table_data_extractor = TableDataExtractor(self.config)
        self.line_detector = LineDetector(self.config)
    
    def extract_tables(self, page, debug_dir=None, file_name="file_name"):
        """
        PDF 페이지에서 테이블을 추출하는 함수
        
        Args:
            page: pdfplumber 페이지 객체
            debug_dir: 시각화 이미지 저장 디렉토리 (기본값: None)
            file_name: 출력 파일 이름 (기본값: "file_name")
            
        Returns:
            추출된 테이블 목록 (2차원 리스트)
        """
        # 디버깅 디렉토리 설정
        if debug_dir:
            os.makedirs(debug_dir, exist_ok=True)

        # 원본 페이지 이미지 생성
        original_img = page.to_image(resolution=self.config.resolution)
        original_img_path = os.path.join(os.getcwd(), "_temp_original_page.png")
        original_img.save(original_img_path)

        # 선을 그린 이미지 생성
        lined_img = page.to_image(resolution=self.config.resolution)
        
        for line in page.lines:
            points = [(line["x0"], line["top"]), (line["x1"], line["bottom"])]
            lined_img.draw_line(points, stroke="red", stroke_width=self.config.line_width)
            
        lined_img_path = os.path.join(os.getcwd(), "_temp_lined_page.png")
        lined_img.save(lined_img_path)

        # 두 이미지를 OpenCV로 로드
        orig_cv = cv2.imread(original_img_path)
        lined_cv = cv2.imread(lined_img_path)

        # 시각화 활성화된 경우 전체 페이지 라인 이미지 저장
        if debug_dir:
            cv2.imwrite(os.path.join(debug_dir, "step1_lined_page.png"), lined_cv)
            # 전체 페이지 병합셀 시각화 이미지 준비
            merged_cells_page = lined_cv.copy()
            
        # 임시 파일 삭제
        try:
            os.remove(original_img_path)
            os.remove(lined_img_path)
        except:
            pass

        # 두 이미지의 차이 계산하여 테이블 선 분리
        diff_img = cv2.absdiff(orig_cv, lined_cv)
        diff_gray = cv2.cvtColor(diff_img, cv2.COLOR_BGR2GRAY)
        
        if debug_dir:
            cv2.imwrite(os.path.join(debug_dir, "step2_diff_page.png"), diff_gray)
            
        _, binary_diff = cv2.threshold(diff_gray, 20, 255, cv2.THRESH_BINARY)

        # 모폴로지 연산으로 선 연결
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        connected = cv2.morphologyEx(binary_diff, cv2.MORPH_CLOSE, kernel, iterations=2)

        # 연결된 구성요소 찾기
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            connected, connectivity=8)

        # 배경(0번 라벨) 제외하고 위에서부터 순서대로 정렬
        areas = stats[1:, cv2.CC_STAT_AREA]
        sorted_indices = np.argsort([stats[i+1, cv2.CC_STAT_TOP] for i in range(len(areas))])
        
        # 테이블 배열
        tables = []

        # 각 테이블 감지 및 처리
        for i, idx in enumerate(sorted_indices):
            component_size = areas[idx]

            # 라벨은 1부터 시작하므로 +1
            component_label = idx + 1
            table_mask = np.zeros_like(binary_diff)
            table_mask[labels == component_label] = 255
            
            # 테이블 외곽 사각형 정보 가져오기
            x = stats[component_label, cv2.CC_STAT_LEFT]
            y = stats[component_label, cv2.CC_STAT_TOP]
            w = stats[component_label, cv2.CC_STAT_WIDTH]
            h = stats[component_label, cv2.CC_STAT_HEIGHT]

            # 테이블 정보 저장
            table_info = {
                'id': i + 1,
                'mask': table_mask,
                'bbox': (x, y, x + w, y + h)
            }

            # 테이블 데이터 추출 전 선 추출
            h_lines, v_lines = self.line_detector.extract_lines_from_mask(table_mask, table_info['id'], debug_dir)

            # 테이블 외곽 경계를 선 정보에 추가
            h_lines, v_lines = self.line_detector.add_table_boundary(h_lines, v_lines, x, y, w, h)

            # 테이블 데이터 추출 (디버깅 정보 포함)
            result = self.table_data_extractor.extract_table_data(
                table_info, lined_cv, page, h_lines, v_lines, debug_dir, file_name)
                
            if result:
                table_data, merged_cells, h_y_coords, v_x_coords, y_offset, x_offset = result
                
                # 테이블 데이터 추가
                tables.append(table_data)
                
                # 시각화 생성 (선택적)
                if debug_dir:
                    # 전체 페이지 병합셀 이미지에 표시
                    for idx, (min_row, min_col, max_row, max_col) in enumerate(merged_cells):
                        color = (0, 255, 0)
                        
                        y0 = int(h_y_coords[min_row])
                        y1 = int(h_y_coords[max_row + 1])
                        x0 = int(v_x_coords[min_col])
                        x1 = int(v_x_coords[max_col + 1])
                        
                        # 병합 그룹 영역 반투명하게 표시
                        overlay = merged_cells_page.copy()
                        cv2.rectangle(overlay, (x0, y0), (x1, y1), color, -1)
                        cv2.addWeighted(overlay, 0.3, merged_cells_page, 0.7, 0, merged_cells_page)
                        
                        # 병합 그룹 경계 강조
                        cv2.rectangle(merged_cells_page, (x0, y0), (x1, y1), color, 1)
                        
                        # 그룹 번호 표시
                        cv2.putText(
                            merged_cells_page, 
                            f"T{i+1}-G{idx+1}", 
                            (x0 + 5, y0 + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1
                        )
                    
                    # 시각화용 전체 페이지에 테이블 영역 표시
                    cv2.rectangle(merged_cells_page, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.putText(
                        merged_cells_page, 
                        f"Table {i+1}", 
                        (x + 5, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2
                    )
                    
                    cv2.imwrite(os.path.join(debug_dir, "step4_merged_cells_page.png"), merged_cells_page)

        return tables
    
    def save_tables_to_excel(self, tables, output_path):
        """
        추출된 테이블을 엑셀 파일로 저장
        
        Args:
            tables: 추출된 테이블 목록
            output_path: 출력 엑셀 파일 경로
        """
        excel_data = []
        
        for table in tables:
            # 행 단위 데이터 추출
            for row in table:
                excel_data.append(row)
            excel_data.append([])  # 테이블 간 공백 행 추가
        
        # 엑셀 저장
        df = pd.DataFrame(excel_data)
        df.to_excel(output_path, index=False, header=False)
        print(f"테이블이 성공적으로 추출되어 {output_path}에 저장되었습니다.")


if __name__ == "__main__":
    pdf_path = r"C:\Users\yunis\바탕 화면\세부사업설명서\세출\2025_02_04254.pdf" 
    page_num = 3
    debug_dir = "table_output"
    
    config = TableExtractorConfig(resolution=150)
    extractor = TableExtractor(config)
    
    with pdfplumber.open(pdf_path) as pdf:       
        page = pdf.pages[page_num]
        file_name = os.path.basename(os.path.splitext(pdf_path)[0])
        
        # 출력 디렉토리 생성
        os.makedirs(debug_dir, exist_ok=True)
        
        # 테이블 추출
        tables = extractor.extract_tables(page, file_name=file_name)
        
        # 엑셀 저장
        output_file = os.path.join(debug_dir, f"{file_name}_tables.xlsx")
        extractor.save_tables_to_excel(tables, output_file)
