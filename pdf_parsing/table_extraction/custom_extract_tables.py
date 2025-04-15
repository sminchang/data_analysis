import pdfplumber
import numpy as np
import cv2
import os
import pandas as pd

# pdfplumber에 비해 개선된 점
# 1. 텍스트 레이어에 맞춰 추출하여, 간혹 화면에 보이지 않는 정보가 추출 -> 화면에 보이는 페이지 정보에 맞춰 추출
# 2. 점선으로 된 테이블 양식에 대해 인식하지 못함 -> 점선 테이블 포함 인식
# 3. 모아찍기 해제된 페이지 내 테이블 좌표가 모아찍기 해제 전 좌표를 유지하는 문제 -> 좌표값 조정 기능을 추가하여 모아찍기 해제 지원

# 주요 동작 원리
# 1. pdfplumber가 테이블 선으로 인식한 lines 객체로 테이블 실제 선을 그리고 이미지화
# 2. 실제 선 이미지를 토대로 마스크만 따서 좌표값 추출
# 3. 마스크 좌표값을 토대로 그리드 선을 그리고 이미지화 (그리드 선은 테이블 내 포함된 선들의 가장 긴 수평-수직 선을 긋는다.)
# 4. 그리드 선 이미지와 실제 선 이미지 사이에 선 유무를 비교하여 그리드 선만 존재하는 셀 영역을 병합셀로 인식시킨다.
# 5. 병합셀에 포함된 그리드 선이 수직선일 때는 좌우병합셀로, 수평선일 때는 상하병합셀로 인식시킨다. 

def extract_lines_from_table_mask(table_mask):
    """테이블 마스크에서 수평선과 수직선을 추출하는 함수"""
    # 선 감지를 위한 전처리
    lines_img = table_mask.copy()
    lines_img = cv2.GaussianBlur(lines_img, (3, 3), 0)  # 노이즈 제거
    edges = cv2.Canny(lines_img, 50, 150, apertureSize=3)  # 엣지 검출
    
    # 허프 변환으로 선 감지 - 파라미터 조정
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180,
                            threshold=30,
                            minLineLength=10,
                            maxLineGap=25)

    # 선 분리
    h_lines = []  # 수평선: (y, x0, x1)
    v_lines = []  # 수직선: (x, y0, y1)

    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            # 선의 각도 계산
            angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
            
            # 수평선 (각도가 0 또는 180에 가까움)
            if angle < 15 or angle > 165:
                h_lines.append((min(y1, y2), min(x1, x2), max(x1, x2)))
            
            # 수직선 (각도가 90에 가까움)
            elif 75 < angle < 105:
                v_lines.append((min(x1, x2), min(y1, y2), max(y1, y2)))

    # 짧은 선 세그먼트 연결
    h_lines = merge_line_segments(h_lines, is_horizontal=True)
    v_lines = merge_line_segments(v_lines, is_horizontal=False)

    # 수평선과 수직선 정렬
    h_lines.sort()  # y 좌표 기준 정렬
    v_lines.sort()  # x 좌표 기준 정렬
    
    return h_lines, v_lines


def merge_line_segments(lines, is_horizontal, gap_threshold=40):
    """가까운 선 세그먼트를 병합하는 함수"""
    if not lines:
        return []
    
    # 좌표 기준으로 정렬
    if is_horizontal:
        lines.sort()  # y 좌표 기준 정렬
    else:
        lines.sort()  # x 좌표 기준 정렬
    
    merged_lines = []
    current_line = lines[0]
    
    for line in lines[1:]:
        if is_horizontal:
            y, x0, x1 = current_line
            y_next, x0_next, x1_next = line
            
            # 같은 y 좌표에 있고 x 좌표가 가까운 경우 병합
            if abs(y - y_next) <= 5 and x0_next - x1 <= gap_threshold:
                current_line = (y, min(x0, x0_next), max(x1, x1_next))
            else:
                merged_lines.append(current_line)
                current_line = line
        else:
            x, y0, y1 = current_line
            x_next, y0_next, y1_next = line
            
            # 같은 x 좌표에 있고 y 좌표가 가까운 경우 병합
            if abs(x - x_next) <= 5 and y0_next - y1 <= gap_threshold:
                current_line = (x, min(y0, y0_next), max(y1, y1_next))
            else:
                merged_lines.append(current_line)
                current_line = line
    
    merged_lines.append(current_line)
    return merged_lines


def merge_coords(coords, threshold=5):
    """좌표 병합 (threshold 픽셀 이내 좌표들을 평균값으로 병합)"""
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


def create_grid_lines(h_y_coords, v_x_coords):
    """그리드 좌표로부터 그리드 라인 생성"""
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


def detect_merged_cells(h_lines, v_lines, grid_h_lines, grid_v_lines, h_y_coords, v_x_coords):
    """실제 선과 그리드 선을 비교하여 병합셀 감지"""
    # 그리드 선과 실제 선 비교를 위한 임계값
    threshold = 5
    
    # 행과 열의 수 계산
    rows = len(h_y_coords) - 1
    cols = len(v_x_coords) - 1
    
    # 셀별 병합 상태를 저장할 매트릭스 초기화
    # 0: 병합되지 않음, 1: 아래쪽과 병합(행 병합), 2: 오른쪽과 병합(열 병합)
    merged_matrix = np.zeros((rows, cols), dtype=int)
    
    # 각 그리드 라인에 대응하는 실제 라인 세그먼트를 찾기
    # 각 수평 그리드 라인에 대해 실제 수평선의 세그먼트들 저장
    h_line_segments = {}  # key: grid_y 값, value: (x0, x1) 세그먼트 목록
    for grid_y, grid_x0, grid_x1 in grid_h_lines:
        h_line_segments[grid_y] = []
        
        # 이 그리드 라인과 일치하는 실제 선 찾기
        for y, x0, x1 in h_lines:
            if abs(y - grid_y) <= threshold:
                # 실제 선 세그먼트 추가
                h_line_segments[grid_y].append((x0, x1))
    
    # 각 수직 그리드 라인에 대해 실제 수직선의 세그먼트들 저장
    v_line_segments = {}  # key: grid_x 값, value: (y0, y1) 세그먼트 목록
    for grid_x, grid_y0, grid_y1 in grid_v_lines:
        v_line_segments[grid_x] = []
        
        # 이 그리드 라인과 일치하는 실제 선 찾기
        for x, y0, y1 in v_lines:
            if abs(x - grid_x) <= threshold:
                # 실제 선 세그먼트 추가
                v_line_segments[grid_x].append((y0, y1))
    
    # 각 셀의 경계선 유무 확인
    for i in range(rows):
        for j in range(cols):
            # 셀의 경계 좌표
            top_y = h_y_coords[i]
            bottom_y = h_y_coords[i + 1]
            left_x = v_x_coords[j]
            right_x = v_x_coords[j + 1]
            
            # 아래쪽 경계선 확인 (행 병합 감지)
            if i < rows - 1:  # 마지막 행이 아닌 경우만
                # 이 셀의 아래쪽 경계선이 존재하는지 확인
                bottom_border_exists = False
                
                # 아래쪽 경계선에 해당하는 그리드 라인
                grid_y = h_y_coords[i + 1]
                
                # 이 그리드 라인에 대응하는 실제 선 세그먼트 확인
                if grid_y in h_line_segments:
                    for x0, x1 in h_line_segments[grid_y]:
                        # 세그먼트가 셀의 x 범위와 충분히 겹치는지 확인
                        if not (x1 < left_x + threshold or x0 > right_x - threshold):
                            # 세그먼트가 셀 너비의 적어도 30% 이상 커버하는지
                            if min(x1, right_x) - max(x0, left_x) >= (right_x - left_x) * 0.3:
                                bottom_border_exists = True
                                break
                
                # 아래쪽 경계선이 없으면 아래 셀과 병합된 것으로 판단
                if not bottom_border_exists:
                    merged_matrix[i, j] = 1  # 아래쪽과 병합
            
            # 오른쪽 경계선 확인 (열 병합 감지)
            if j < cols - 1:  # 마지막 열이 아닌 경우만
                # 이 셀의 오른쪽 경계선이 존재하는지 확인
                right_border_exists = False
                
                # 오른쪽 경계선에 해당하는 그리드 라인
                grid_x = v_x_coords[j + 1]
                
                # 이 그리드 라인에 대응하는 실제 선 세그먼트 확인
                if grid_x in v_line_segments:
                    for y0, y1 in v_line_segments[grid_x]:
                        # 세그먼트가 셀의 y 범위와 충분히 겹치는지 확인
                        if not (y1 < top_y + threshold or y0 > bottom_y - threshold):
                            # 세그먼트가 셀 높이의 적어도 30% 이상 커버하는지
                            if min(y1, bottom_y) - max(y0, top_y) >= (bottom_y - top_y) * 0.3:
                                right_border_exists = True
                                break
                
                # 오른쪽 경계선이 없으면 오른쪽 셀과 병합된 것으로 판단
                if not right_border_exists:
                    # 이미 아래쪽과 병합된 셀은 우선순위가 있으므로 유지
                    if merged_matrix[i, j] == 0:
                        merged_matrix[i, j] = 2  # 오른쪽과 병합
    
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
                
                # 아래쪽과 병합된 경우
                if r < rows - 1 and merged_matrix[r, c] == 1 and not visited[r + 1, c]:
                    visited[r + 1, c] = True
                    group.append((r + 1, c))
                    queue.append((r + 1, c))
                    max_row = max(max_row, r + 1)
                
                # 오른쪽과 병합된 경우
                if c < cols - 1 and merged_matrix[r, c] == 2 and not visited[r, c + 1]:
                    visited[r, c + 1] = True
                    group.append((r, c + 1))
                    queue.append((r, c + 1))
                    max_col = max(max_col, c + 1)
            
            # 병합 그룹 정보 저장
            if len(group) > 1:
                merged_groups.append((min_row, min_col, max_row, max_col))

    return merged_groups


def visualize_merged_cells(table_data, merged_cells, h_y_coords, v_x_coords, table_img, y_offset, x_offset, output_path):
    """병합셀을 시각화하여 이미지로 저장하는 함수"""
    # 테이블 데이터의 행과 열 수
    rows = len(table_data)
    cols = len(table_data[0]) if rows > 0 else 0
    
    # 병합셀 시각화 이미지 생성
    merged_cells_viz = table_img.copy()
    
    # 병합 그룹별로 시각화
    for idx, (min_row, min_col, max_row, max_col) in enumerate(merged_cells):
        color = (0, 255, 0)
        
        # 그룹의 경계 계산
        y0 = int(h_y_coords[min_row] - y_offset)
        y1 = int(h_y_coords[max_row + 1] - y_offset)
        x0 = int(v_x_coords[min_col] - x_offset)
        x1 = int(v_x_coords[max_col + 1] - x_offset)
        
        # 병합 그룹 영역 반투명하게 표시
        overlay = merged_cells_viz.copy()
        cv2.rectangle(overlay, (x0, y0), (x1, y1), color, -1)
        cv2.addWeighted(overlay, 0.3, merged_cells_viz, 0.7, 0, merged_cells_viz)
        
        # 병합 그룹 경계 강조
        cv2.rectangle(merged_cells_viz, (x0, y0), (x1, y1), color, 2)
        
        # 그룹 번호 표시
        cv2.putText(merged_cells_viz, f"Group {idx+1}", (x0 + 5, y0 + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    # 병합셀 시각화 이미지 저장
    cv2.imwrite(output_path, merged_cells_viz)


def extract_table_data(table_info, lined_cv, page, debug_dir=None, file_name="file_name"):
    """개별 테이블 영역에서 데이터 추출 (특정 셀 단위 병합셀 처리)"""
    table_id = table_info['id']
    table_mask = table_info['mask']
    x, y, x_end, y_end = table_info['bbox']
    if debug_dir:
        os.makedirs(debug_dir, exist_ok=True)
        cv2.imwrite(os.path.join(debug_dir, f"table{table_id}_mask.png"), table_mask)

    # 테이블 영역 내의 선 추출
    h_lines, v_lines = extract_lines_from_table_mask(table_mask)

    # 추출된 선 정보로부터 좌표 추출
    h_y_coords = sorted(set([line[0] for line in h_lines]))
    v_x_coords = sorted(set([line[0] for line in v_lines]))

    # 가까운 좌표 병합
    h_y_coords = merge_coords(h_y_coords)
    v_x_coords = merge_coords(v_x_coords)

    # 테이블 구조 유효성 검사
    rows = len(h_y_coords) - 1
    cols = len(v_x_coords) - 1

    if rows <= 0 or cols <= 0:
        return None
    
    # 그리드 라인 생성
    grid_h_lines, grid_v_lines = create_grid_lines(h_y_coords, v_x_coords)
    
    # 디버깅 이미지 생성 (선택적)
    if debug_dir:
        os.makedirs(debug_dir, exist_ok=True)
        # 테이블 영역 추출
        table_img = lined_cv[y:y_end, x:x_end].copy()
    
    # 병합셀 감지 (특정 셀 단위)
    merged_cells = detect_merged_cells(h_lines, v_lines, grid_h_lines, grid_v_lines, h_y_coords, v_x_coords)
    
    # 이미지 해상도에 맞게 좌표 변환 (이미지 좌표 → PDF 좌표)
    resolution_ratio = page.height / lined_cv.shape[0]
    h_y_coords_pdf = [y_coord * resolution_ratio for y_coord in h_y_coords]
    v_x_coords_pdf = [x_coord * resolution_ratio for x_coord in v_x_coords]

    # 테이블 데이터 추출
    table_data = [['' for _ in range(cols)] for _ in range(rows)]
    
    # 셀 패딩
    padding = 2.5 * resolution_ratio
    
    # 병합셀 처리를 위한 변수
    processed_cells = set()
    
    # 병합 그룹별 데이터 추출
    for min_row, min_col, max_row, max_col in merged_cells:
        # 병합 영역의 좌표 계산
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
        
        try:
            cell_text = page.crop(cell_bbox).extract_text() or ''
            cell_text = cell_text.strip()
            
            # 병합 그룹의 대표 셀(좌상단)에 데이터 배치
            table_data[min_row][min_col] = cell_text
            
            # 그룹의 모든 셀을 처리 완료로 표시
            for row in range(min_row, max_row + 1):
                for col in range(min_col, max_col + 1):
                    processed_cells.add((row, col))
        except Exception as e:
            print(f"{file_name}병합셀 추출 오류 ({min_row}-{max_row}, {min_col}-{max_col}): {e}")
    
    # 일반 셀 데이터 추출
    for i in range(rows):
        for j in range(cols):
            # 이미 처리된 셀은 건너뛰기
            if (i, j) in processed_cells:
                continue
            
            # 셀 경계 정의 (PDF 좌표계)
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
            
            try:
                cell_text = page.crop(cell_bbox).extract_text() or ''
                table_data[i][j] = cell_text.strip()
            except Exception as e:
                print(f"{file_name}셀 추출 오류 ({i}, {j}): {e}")
    
    # 디버깅 시각화를 위한 정보도 함께 반환
    if debug_dir:
        return table_data, merged_cells, h_y_coords, v_x_coords, table_img, y, x
    else:
        return table_data, merged_cells, None, None, None, None, None


def extract_tables(page, resolution=150, fill_merged_cells=False, output_dir=None, file_name="file_name"):
    """
    PDF 페이지에서 테이블을 추출하는 함수
    
    Args:
        page: pdfplumber 페이지 객체
        resolution: 이미지 해상도 (기본값: 150)
        fill_merged_cells: 병합셀 값을 모든 분할셀에 복사할지 여부 (기본값: False)
        output_dir: 시각화 이미지 저장 디렉토리 (기본값: None)
        
    Returns:
        추출된 테이블 목록 (2차원 리스트)
    """
    # 디버깅 디렉토리 설정
    debug_dir = output_dir
    if debug_dir:
        os.makedirs(debug_dir, exist_ok=True)

    # 원본 페이지 이미지 생성
    original_img = page.to_image(resolution=resolution)
    original_img_path = os.path.join(os.getcwd(), "_temp_original_page.png")
    original_img.save(original_img_path)

    # 선을 그린 이미지 생성
    lined_img = page.to_image(resolution=resolution)
    line_width = 2
    
    for line in page.lines:
        points = [(line["x0"], line["top"]), (line["x1"], line["bottom"])]
        lined_img.draw_line(points, stroke="red", stroke_width=line_width)
        
    lined_img_path = os.path.join(os.getcwd(), "_temp_lined_page.png")
    lined_img.save(lined_img_path)

    # 두 이미지를 OpenCV로 로드
    orig_cv = cv2.imread(original_img_path)
    lined_cv = cv2.imread(lined_img_path)

    # 시각화 활성화된 경우 전체 페이지 라인 이미지 저장
    if debug_dir:
        cv2.imwrite(os.path.join(debug_dir, "lined_page.png"), lined_cv)
        # 실제 선-그리드 선 시각화 이미지 준비
        grid_viz_page = lined_cv.copy()
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
    _, binary_diff = cv2.threshold(diff_gray, 20, 255, cv2.THRESH_BINARY)

    # 모폴로지 연산으로 선 연결
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (6, 6))
    connected = cv2.morphologyEx(binary_diff, cv2.MORPH_CLOSE, kernel, iterations=2)

    # 연결된 구성요소 찾기
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(connected, connectivity=8)

    # 배경(0번 라벨) 제외하고 위에서부터 순서대로 정렬
    areas = stats[1:, cv2.CC_STAT_AREA]
    sorted_indices = np.argsort([stats[i+1, cv2.CC_STAT_TOP] for i in range(len(areas))])

    # 테이블로 간주할 최소 크기 (픽셀 수)
    min_table_size = 4000 
    
    # 테이블 배열
    tables = []
    max_tables = 10  # 최대 처리할 테이블 수

    # 각 테이블 감지 및 처리
    for i, idx in enumerate(sorted_indices):
        component_size = areas[idx]
        
        if component_size < min_table_size:
            continue  # 너무 작은 영역은 테이블이 아님

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
        
        # 테이블 데이터 추출 (디버깅 정보 포함)
        result = extract_table_data(table_info, lined_cv, page, debug_dir, file_name)
        if result:
            table_data, merged_cells, h_y_coords, v_x_coords, table_img, y_offset, x_offset = result
            
            # 시각화 생성 (선택적) - 개별 테이블의 merged_cells.png는 생성하지 않음
            if debug_dir and merged_cells:

                # 실제 선-그리드 선 이미지에 표시
                for y_coord in h_y_coords:
                            cv2.line(grid_viz_page, 
                                (int(v_x_coords[0]), int(y_coord)),
                                (int(v_x_coords[-1]), int(y_coord)),
                                (255, 0, 255), 1)  # 자주색 선
                for x_coord in v_x_coords:
                    cv2.line(grid_viz_page, 
                        (int(x_coord), int(h_y_coords[0])),
                        (int(x_coord), int(h_y_coords[-1])),
                        (255, 0, 255), 1)  # 자주색 선

                # 전체 페이지 병합셀 이미지에 표시
                for idx, (min_row, min_col, max_row, max_col) in enumerate(merged_cells):
                    color = (0, 255, 0)  # 녹색
                    
                    # 그룹의 경계 계산 - 페이지 좌표계로 변환
                    y0 = int(h_y_coords[min_row])
                    y1 = int(h_y_coords[max_row + 1])
                    x0 = int(v_x_coords[min_col])
                    x1 = int(v_x_coords[max_col + 1])
                    
                    # 병합 그룹 영역 반투명하게 표시
                    overlay = merged_cells_page.copy()
                    cv2.rectangle(overlay, (x0, y0), (x1, y1), color, -1)
                    cv2.addWeighted(overlay, 0.3, merged_cells_page, 0.7, 0, merged_cells_page)
                    
                    # 병합 그룹 경계 강조
                    cv2.rectangle(merged_cells_page, (x0, y0), (x1, y1), color, 2)
                    
                    # 그룹 번호 표시
                    cv2.putText(merged_cells_page, f"T{i+1}-G{idx+1}", (x0 + 5, y0 + 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            if fill_merged_cells and merged_cells:
                # 병합셀 값을 모든 분할셀에 복사
                for min_row, min_col, max_row, max_col in merged_cells:
                    value = table_data[min_row][min_col]
                    for row in range(min_row, max_row + 1):
                        for col in range(min_col, max_col + 1):
                            table_data[row][col] = value
            
            # 테이블 데이터 추가
            tables.append(table_data)
            
            # 시각화용 전체 페이지에 테이블 영역 표시
            if debug_dir:
                # 테이블 경계 표시 (빨간색)
                cv2.rectangle(merged_cells_page, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(merged_cells_page, f"Table {i+1}", (x + 5, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        if len(tables) >= max_tables:  # 최대 max_tables개 테이블만 처리
            break
    
    # 전체 페이지 병합셀 시각화 이미지 저장
    if debug_dir:
        cv2.imwrite(os.path.join(debug_dir, "merged_cells_page.png"), merged_cells_page)
        cv2.imwrite(os.path.join(debug_dir, "grid_lines_page.png"), grid_viz_page)

    return tables


# 사용 예시
if __name__ == "__main__":
    pdf_path = r"C:\Users\yunis\바탕 화면\test\2025_02_00153.pdf"
    excel_data = []
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[2]
        file_name = os.path.splitext(pdf_path)[0]
        
        # 병합셀 값 복사 없이 테이블 추출
        tables = extract_tables(page, output_dir="table_output")
        
        for table in tables:
            #행 단위 데이터 추출
            for row in table:
                excel_data.append(row)
            excel_data.append([]) # 테이블 간 공백 행 추가

    #엑셀 저장
    df = pd.DataFrame(excel_data)
    df.to_excel(f"test_table.xlsx", index=False, header=False)
