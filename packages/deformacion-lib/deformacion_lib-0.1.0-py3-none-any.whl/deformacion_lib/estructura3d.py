import cv2
import numpy as np
import os
import glob
import csv
import shutil
from PIL import Image
import matplotlib.pyplot as plt


def extract_frames(video_path, n_frames, ext=".png", frames_out="ExtractedFrames"):
    """Extrae n_frames equidistantes del video."""
    if os.path.exists(frames_out):
        shutil.rmtree(frames_out)
    os.makedirs(frames_out)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"No se puede abrir el video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        raise ValueError("Conteo de frames inválido")

    n_frames = min(n_frames, total_frames)
    frame_indices = np.linspace(0, total_frames - 1, n_frames, dtype=int)

    saved = 0
    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue

        filename = f"frame_{saved:06d}{ext}"
        cv2.imwrite(os.path.join(frames_out, filename), frame)
        saved += 1

    cap.release()
    print(f"✅ {saved} frames extraídos")
    return saved


def crop_images(image_pattern, output_dir="CroppedImages"):
    """Recorta todas las imágenes usando ROI seleccionado en la primera."""
    image_paths = sorted(glob.glob(image_pattern))
    if not image_paths:
        raise RuntimeError(f"No se encontraron imágenes: {image_pattern}")

    img0 = cv2.imread(image_paths[0])
    if img0 is None:
        raise RuntimeError("Error al leer la primera imagen")

    cv2.namedWindow("Select ROI", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Select ROI", 1000, 800)
    x, y, w, h = cv2.selectROI("Select ROI", img0, showCrosshair=True)
    cv2.destroyAllWindows()

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    for i, path in enumerate(image_paths):
        img = cv2.imread(path)
        if img is None:
            continue
        roi = img[y:y+h, x:x+w]
        cv2.imwrite(os.path.join(output_dir, f"crop_{i:04d}.png"), roi)

    print(f"✅ {len(image_paths)} imágenes recortadas")


def detect_edges(input_dir, output_dir, black_threshold=40, blur_kernel=5):
    """
    Detecta todos los píxeles negros (estructura).
    Aplica blur para mejorar detección en videos rápidos.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    image_paths = sorted(glob.glob(os.path.join(input_dir, "*.png")))
    if not image_paths:
        image_paths = sorted(glob.glob(os.path.join(input_dir, "*.tif")))
    if not image_paths:
        raise RuntimeError(f"No hay imágenes en {input_dir}")
    
    edge_data = {}
    
    for i, img_path in enumerate(image_paths):
        img = cv2.imread(img_path)
        if img is None:
            continue
        
        output_img = img.copy()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        blurred = cv2.GaussianBlur(gray, (blur_kernel, blur_kernel), 0)
        _, black_mask = cv2.threshold(blurred, black_threshold, 255, cv2.THRESH_BINARY_INV)
        
        kernel = np.ones((2, 2), np.uint8)
        black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        
        edge_pixels = [[int(p[1]), int(p[0])] for p in np.argwhere(black_mask == 255)]
        
        output_img[black_mask == 255] = (0, 255, 0)
        
        filename = f"frame_{i:04d}"
        cv2.imwrite(os.path.join(output_dir, f"{filename}_edges.png"), output_img)
        cv2.imwrite(os.path.join(output_dir, f"{filename}_mask.png"), black_mask)
        
        edge_data[filename] = {
            "original_image": img_path,
            "edge_pixels": edge_pixels,
            "index": i,
            "has_data": len(edge_pixels) > 0
        }
        
        if len(edge_pixels) > 0:
            print(f"   Frame {i}: {len(edge_pixels)} píxeles detectados")
        else:
            print(f"   Frame {i}: ⚠️ Sin píxeles detectados")
    
    print(f"✅ {len(edge_data)} frames procesados")
    return edge_data


def extract_left_and_right_walls(edge_pixels, image_width):
    """
    Extrae dos líneas de píxeles:
    - Línea izquierda: mitad izquierda, píxel más a la derecha por cada Y
    - Línea derecha: mitad derecha, píxel más a la derecha por cada Y
    """
    if not edge_pixels:
        return {}, {}
    
    pixels_array = np.array(edge_pixels)
    mid_x = image_width // 2
    
    left_pixels = pixels_array[pixels_array[:, 0] < mid_x]
    right_pixels = pixels_array[pixels_array[:, 0] >= mid_x]
    
    left_wall = {}
    right_wall = {}
    
    if len(left_pixels) > 0:
        for y in np.unique(left_pixels[:, 1]):
            pixels_at_y = left_pixels[left_pixels[:, 1] == y]
            left_wall[int(y)] = int(pixels_at_y[:, 0].max())
    
    if len(right_pixels) > 0:
        for y in np.unique(right_pixels[:, 1]):
            pixels_at_y = right_pixels[right_pixels[:, 1] == y]
            right_wall[int(y)] = int(pixels_at_y[:, 0].max())
    
    return left_wall, right_wall


def analyze_deformation(edge_data, real_size_total_mm, test_duration_s=None, min_presence=0.8):
    frame_keys = sorted(edge_data.keys())
    if not frame_keys:
        raise RuntimeError("No hay frames para analizar")
    
    frames_with_data = [fk for fk in frame_keys if edge_data[fk]["has_data"]]
    if not frames_with_data:
        raise RuntimeError("Ningún frame tiene píxeles detectados")
    
    first_img = cv2.imread(edge_data[frame_keys[0]]["original_image"])
    h, w = first_img.shape[:2]
    
    real_size_mm = real_size_total_mm - 5.0
    
    print(f"\n🔍 Extrayendo paredes izquierda y derecha...")
    left_walls = {}
    right_walls = {}
    
    for fk in frame_keys:
        lw, rw = extract_left_and_right_walls(edge_data[fk]["edge_pixels"], w)
        left_walls[fk] = lw
        right_walls[fk] = rw
    
    ref_frame = frame_keys[0]
    for fk in frame_keys:
        if left_walls[fk] and right_walls[fk]:
            ref_frame = fk
            break
    
    if not left_walls[ref_frame] or not right_walls[ref_frame]:
        raise RuntimeError("No se encontró frame con ambas paredes")
    
    print(f"📌 Frame de referencia: {ref_frame}")
    
    ref_left = left_walls[ref_frame]
    ref_right = right_walls[ref_frame]
    
    all_y = sorted(ref_right.keys())
    if not all_y:
        raise RuntimeError("No hay datos en línea derecha de referencia")
    
    y_min, y_max = all_y[0], all_y[-1]
    y_range = y_max - y_min
    y_start = int(y_min + y_range * 0.125)
    y_end = int(y_max - y_range * 0.125)
    valid_y_range = [y for y in all_y if y_start <= y <= y_end]
    
    print(f"🔍 Rango Y válido: {y_start} a {y_end} (75% central, {len(valid_y_range)} puntos)")
    
    total_frames = len(frame_keys)
    min_frames_required = int(total_frames * min_presence)
    
    y_presence_count = {}
    for y in valid_y_range:
        count = sum(1 for fk in frame_keys if y in right_walls[fk])
        y_presence_count[y] = count
    
    valid_y = [y for y in valid_y_range if y_presence_count[y] >= min_frames_required]
    
    if not valid_y:
        raise RuntimeError(f"Ninguna línea Y aparece en ≥{min_presence*100}% de los frames")
    
    print(f"✅ Líneas Y válidas: {len(valid_y)} de {len(valid_y_range)}")
    
    valid_y_left = [y for y in valid_y if y in ref_left]
    if not valid_y_left:
        raise RuntimeError("No hay datos de pared izquierda en rango Y válido")
    
    max_x_left = max([ref_left[y] for y in valid_y_left])
    max_x_right = max([ref_right[y] for y in valid_y if y in ref_right])
    
    initial_width_px = max_x_right - max_x_left
    px_to_mm = real_size_mm / initial_width_px
    
    print(f"\n🔬 CALIBRACIÓN:")
    print(f"   Distancia total ingresada: {real_size_total_mm} mm")
    print(f"   Pared izquierda: 5.0 mm")
    print(f"   Distancia medible: {real_size_mm} mm")
    print(f"   Pared izq (max X): {max_x_left} px")
    print(f"   Pared der (max X): {max_x_right} px")
    print(f"   Distancia inicial: {initial_width_px:.2f} px = {real_size_mm} mm")
    print(f"   Escala: 1 px = {px_to_mm:.6f} mm\n")
    
    print("🎯 Buscando punto de máxima compresión...")
    max_compression_px = 0
    max_compression_y = None
    
    for fk in frame_keys:
        rw = right_walls[fk]
        for y in valid_y:
            if y in ref_right and y in rw:
                compression = ref_right[y] - rw[y]
                if compression > max_compression_px:
                    max_compression_px = compression
                    max_compression_y = y
    
    if max_compression_y is None:
        max_compression_y = valid_y[len(valid_y)//2]
        print(f"⚠️ No se detectó compresión - usando centro: Y={max_compression_y}")
    else:
        print(f"✅ Punto Y de máxima compresión: {max_compression_y}")
        print(f"   Compresión máxima: {max_compression_px:.2f} px")
    
    if max_compression_y not in ref_left or max_compression_y not in ref_right:
        raise RuntimeError(f"No hay datos en Y={max_compression_y} en frame de referencia")
    
    ref_width_at_y = ref_right[max_compression_y] - ref_left[max_compression_y]
    
    results = []
    
    for fk in frame_keys:
        lw = left_walls[fk]
        rw = right_walls[fk]
        
        frame_idx = edge_data[fk]["index"]
        if test_duration_s is not None:
            time_s = (frame_idx / (len(frame_keys) - 1)) * test_duration_s if len(frame_keys) > 1 else 0
        else:
            time_s = frame_idx
        
        if max_compression_y in lw and max_compression_y in rw:
            current_width_px = rw[max_compression_y] - lw[max_compression_y]
            compression_px = ref_width_at_y - current_width_px
            compression_mm = compression_px * px_to_mm
            strain = compression_mm / real_size_mm
            
            results.append({
                "frame": frame_idx,
                "time_s": float(time_s),
                "compression_px": float(compression_px),
                "compression_mm": float(compression_mm),
                "strain": float(strain),
                "width_px": float(current_width_px),
                "width_mm": float(current_width_px * px_to_mm),
                "has_data": True
            })
        else:
            results.append({
                "frame": frame_idx,
                "time_s": float(time_s),
                "compression_px": None,
                "compression_mm": None,
                "strain": None,
                "width_px": None,
                "width_mm": None,
                "has_data": False
            })
    
    return {
        "px_to_mm": px_to_mm,
        "tracked_y": max_compression_y,
        "initial_width_px": ref_width_at_y,
        "results": results,
        "left_walls": left_walls,
        "right_walls": right_walls,
        "image_width": w,
        "image_height": h,
        "valid_y_range": (y_start, y_end),
        "valid_y": valid_y
    }


def save_results(analysis, edge_data, results_dir, duracion_gifs=2.0):
    """Guarda todos los resultados en la estructura de carpetas especificada."""
    os.makedirs(results_dir, exist_ok=True)
    
    analysis_dir = os.path.join(results_dir, "Analysis")
    os.makedirs(analysis_dir, exist_ok=True)
    
    valid_results = [r for r in analysis["results"] if r.get("has_data", True) and r["compression_mm"] is not None]
    
    if not valid_results:
        print("⚠️ No hay datos válidos")
        return
    
    compressions = [r["compression_mm"] for r in valid_results]
    
    start_idx = 0
    for i in range(1, len(compressions)):
        if abs(compressions[i] - compressions[0]) > 0.01:
            start_idx = i - 1
            break
    
    end_idx = len(compressions) - 1
    for i in range(len(compressions) - 2, -1, -1):
        if abs(compressions[i] - compressions[-1]) > 0.01:
            end_idx = i + 1
            break
    
    trimmed_results = valid_results[start_idx:end_idx+1]
    
    print(f"📊 Datos recortados: frames {trimmed_results[0]['frame']} a {trimmed_results[-1]['frame']}")
    print(f"   ({len(trimmed_results)} de {len(valid_results)} frames)")
    
    csv_path = os.path.join(analysis_dir, "deformation_data.csv")
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["frame", "time_s", "compression_px", "compression_mm", "strain", "width_mm"])
        writer.writeheader()
        
        for r in trimmed_results:
            writer.writerow({
                "frame": r["frame"],
                "time_s": r["time_s"],
                "compression_px": r["compression_px"],
                "compression_mm": r["compression_mm"],
                "strain": r["strain"],
                "width_mm": r["width_mm"]
            })
    print(f"✅ CSV: {csv_path}")
    
    time_s = [r["time_s"] for r in trimmed_results]
    comp_mm = [r["compression_mm"] for r in trimmed_results]
    strain = [r["strain"] for r in trimmed_results]
    
    if time_s:
        time_offset = time_s[0]
        time_s = [t - time_offset for t in time_s]
    
    fig1, ax1 = plt.subplots(figsize=(8, 6))
    ax1.plot(time_s, strain, 'b-', linewidth=2)
    ax1.set_title("Strain vs Time", fontsize=14, fontweight='bold')
    ax1.set_xlabel("Time [s]", fontsize=12)
    ax1.set_ylabel("Strain [-]", fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(bottom=0)
    plt.tight_layout()
    plt.savefig(os.path.join(analysis_dir, "strain_vs_time.png"), dpi=200)
    plt.close()
    
    fig2, ax2 = plt.subplots(figsize=(8, 6))
    ax2.plot(time_s, comp_mm, 'r-', linewidth=2)
    ax2.set_title("Elongation vs Time", fontsize=14, fontweight='bold')
    ax2.set_xlabel("Time [s]", fontsize=12)
    ax2.set_ylabel("Elongation [mm]", fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(bottom=0)
    plt.tight_layout()
    plt.savefig(os.path.join(analysis_dir, "elongation_vs_time.png"), dpi=200)
    plt.close()
    
    print(f"✅ Gráficas guardadas: {analysis_dir}")
    
    raw_dir = os.path.join(results_dir, "Raw_Processing")
    os.makedirs(raw_dir, exist_ok=True)
    
    edges_dir = os.path.join(raw_dir, "EdgesOnPhoto")
    if os.path.exists(edges_dir):
        shutil.rmtree(edges_dir)
    shutil.copytree("TempEdges", edges_dir, ignore=shutil.ignore_patterns('*_mask.png'))
    print(f"✅ Bordes en fotos: {edges_dir}")
    
    lines_dir = os.path.join(raw_dir, "Lines")
    os.makedirs(lines_dir, exist_ok=True)
    
    frame_keys = sorted(edge_data.keys())
    h, w = analysis["image_height"], analysis["image_width"]
    tracked_y = analysis["tracked_y"]
    valid_y = analysis["valid_y"]
    
    for fk in frame_keys:
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        
        lw = analysis["left_walls"][fk]
        for y, x in lw.items():
            if y in valid_y:
                cv2.circle(canvas, (x, y), 2, (255, 0, 0), -1)
        
        rw = analysis["right_walls"][fk]
        for y, x in rw.items():
            if y in valid_y:
                cv2.circle(canvas, (x, y), 2, (0, 255, 0), -1)
        
        cv2.imwrite(os.path.join(lines_dir, f"{fk}_lines.png"), canvas)
    
    print(f"✅ Líneas (75% central): {lines_dir}")
    
    viz_dir = os.path.join(results_dir, "Visualization")
    os.makedirs(viz_dir, exist_ok=True)
    
    edges_files = sorted(glob.glob("TempEdges/*_edges.png"))
    if edges_files:
        edges_imgs = [Image.open(f) for f in edges_files]
        gif_path = os.path.join(viz_dir, "deformation_animation.gif")
        duration = int((duracion_gifs / len(edges_imgs)) * 1000)
        edges_imgs[0].save(gif_path, save_all=True, append_images=edges_imgs[1:], duration=duration, loop=0)
        print(f"✅ GIF deformación: {gif_path}")
    
    line_frames = []
    for fk in frame_keys:
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        
        lw = analysis["left_walls"][fk]
        for y, x in lw.items():
            if y in valid_y:
                cv2.circle(canvas, (x, y), 2, (255, 0, 0), -1)
        
        rw = analysis["right_walls"][fk]
        for y, x in rw.items():
            if y in valid_y:
                cv2.circle(canvas, (x, y), 2, (0, 255, 0), -1)
        
        if tracked_y in lw and tracked_y in rw:
            x_left = lw[tracked_y]
            x_right = rw[tracked_y]
            cv2.line(canvas, (x_left, tracked_y), (x_right, tracked_y), (0, 255, 255), 2)
            
            result = next((r for r in analysis["results"] if edge_data[fk]["index"] == r["frame"]), None)
            if result and result.get("width_mm") is not None:
                text = f"{result['width_mm']:.2f} mm"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6
                thickness = 2
                text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
                text_x = (w - text_size[0]) // 2
                text_y = max(30, tracked_y - 10)
                cv2.putText(canvas, text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness)
        
        line_frames.append(Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)))
    
    gif_lines_path = os.path.join(viz_dir, "tracking_lines.gif")
    duration = int((duracion_gifs / len(line_frames)) * 1000)
    line_frames[0].save(gif_lines_path, save_all=True, append_images=line_frames[1:], duration=duration, loop=0)
    print(f"✅ GIF líneas: {gif_lines_path}")
    
    first_frame_key = frame_keys[0]
    last_frame_key = frame_keys[-1]
    
    first_img = cv2.imread(edge_data[first_frame_key]["original_image"])
    last_img = cv2.imread(edge_data[last_frame_key]["original_image"])
    
    blended = cv2.addWeighted(first_img, 0.5, last_img, 0.5, 0)
    
    lw_first = analysis["left_walls"][first_frame_key]
    rw_first = analysis["right_walls"][first_frame_key]
    lw_last = analysis["left_walls"][last_frame_key]
    rw_last = analysis["right_walls"][last_frame_key]
    
    if tracked_y in lw_first and tracked_y in rw_first:
        x_left_init = lw_first[tracked_y]
        x_right_init = rw_first[tracked_y]
        cv2.circle(blended, (x_right_init, tracked_y), 6, (0, 255, 0), -1)
        cv2.circle(blended, (x_right_init, tracked_y), 6, (255, 255, 255), 1)
    
    if tracked_y in lw_last and tracked_y in rw_last:
        x_right_final = rw_last[tracked_y]
        cv2.circle(blended, (x_right_final, tracked_y), 6, (0, 0, 255), -1)
        cv2.circle(blended, (x_right_final, tracked_y), 6, (255, 255, 255), 1)
    
    cv2.imwrite(os.path.join(viz_dir, "measurement_point.png"), blended)
    print(f"✅ Punto de medición: {viz_dir}/measurement_point.png")
    
    comparison = np.zeros((h, w, 3), dtype=np.uint8)
    
    for y, x in lw_first.items():
        if y in valid_y:
            cv2.circle(comparison, (x, y), 1, (255, 0, 0), -1)
    
    for y, x in rw_first.items():
        if y in valid_y:
            cv2.circle(comparison, (x, y), 1, (0, 255, 0), -1)
    
    for y, x in rw_last.items():
        if y in valid_y:
            cv2.circle(comparison, (x, y), 1, (0, 0, 255), -1)
    
    cv2.imwrite(os.path.join(viz_dir, "wall_comparison.png"), comparison)
    print(f"✅ Comparación de paredes: {viz_dir}/wall_comparison.png")
    
    print(f"\n{'='*60}")
    print(f"📁 ESTRUCTURA DE RESULTADOS:")
    print(f"   {results_dir}/")
    print(f"   ├── 📊 deformation_data.csv")
    print(f"   ├── 📈 Analysis/")
    print(f"   │   ├── strain_vs_time.png")
    print(f"   │   └── elongation_vs_time.png")
    print(f"   ├── 🔬 Raw_Processing/")
    print(f"   │   ├── EdgesOnPhoto/")
    print(f"   │   └── Lines/")
    print(f"   └── 🎬 Visualization/")
    print(f"       ├── deformation_animation.gif")
    print(f"       ├── tracking_lines.gif")
    print(f"       ├── measurement_point.png")
    print(f"       └── wall_comparison.png")
    print(f"{'='*60}\n")


def ejecutar_analisis_3d(
    modo,
    nombre_archivo,
    tiempo_experimento,
    distancia_total_mm,
    n_frames=None,
    ext_imagen=".png",
    base_dir=None,
    duracion_gifs=2.0
):
    """
    Función principal para análisis de estructuras 3D impresas.
    
    Parámetros:
    modo: "video" o "foto"
    nombre_archivo: nombre del video o carpeta de imágenes
    tiempo_experimento: duración del experimento en segundos
    distancia_total_mm: distancia total real (incluye 5mm de pared izquierda)
    n_frames: número de frames a extraer (solo para modo video)
    ext_imagen: extensión de las imágenes
    base_dir: directorio base
    duracion_gifs: duración de los GIFs en segundos (1-3 recomendado)
    """
    if base_dir is None:
        base_dir = os.getcwd()
    
    FRAMES_DIR = os.path.join(base_dir, "ExtractedFrames")
    CROPPED_DIR = os.path.join(base_dir, "CroppedImages")
    TEMP_EDGES_DIR = os.path.join(base_dir, "TempEdges")
    
    RESULTS_DIR = os.path.join(base_dir, "Results (3D Printed Body Program)")
    
    print(f"\n{'='*60}")
    print(f"ANÁLISIS DE ESTRUCTURA 3D")
    print(f"{'='*60}")
    print(f"Modo: {modo}")
    print(f"Archivo: {nombre_archivo}")
    print(f"Tiempo experimento: {tiempo_experimento} s")
    print(f"Distancia total: {distancia_total_mm} mm")
    print(f"Distancia medible: {distancia_total_mm - 5.0} mm (restando pared izq)")
    print(f"{'='*60}\n")
    
    if modo.lower() == "video":
        if n_frames is None:
            raise ValueError("Debes especificar n_frames para modo video")
        
        video_path = os.path.join(base_dir, nombre_archivo)
        print(f"PASO 1/5: Extrayendo {n_frames} frames del video...")
        extract_frames(video_path, n_frames, ext_imagen, FRAMES_DIR)
        frames_dir = FRAMES_DIR
    else:
        frames_dir = os.path.join(base_dir, nombre_archivo)
        print(f"PASO 1/5: Usando imágenes de: {frames_dir}")
    
    print("\nPASO 2/5: Selecciona el ROI...")
    crop_images(os.path.join(frames_dir, f"*{ext_imagen}"), CROPPED_DIR)
    
    print("\nPASO 3/5: Detectando bordes...")
    edge_data = detect_edges(CROPPED_DIR, TEMP_EDGES_DIR)
    
    print("\nPASO 4/5: Analizando deformación...")
    analysis = analyze_deformation(edge_data, distancia_total_mm, tiempo_experimento)
    
    print("\nPASO 5/5: Generando outputs...")
    save_results(analysis, edge_data, RESULTS_DIR, duracion_gifs)
    
    print("\n🗑️ Limpiando archivos temporales...")
    if os.path.exists(FRAMES_DIR):
        shutil.rmtree(FRAMES_DIR)
    if os.path.exists(CROPPED_DIR):
        shutil.rmtree(CROPPED_DIR)
    if os.path.exists(TEMP_EDGES_DIR):
        shutil.rmtree(TEMP_EDGES_DIR)
    print("✅ Carpetas temporales eliminadas")
    print(f"\n{'='*60}")
    print("✅ ANÁLISIS COMPLETADO EXITOSAMENTE")
    print(f"{'='*60}\n")