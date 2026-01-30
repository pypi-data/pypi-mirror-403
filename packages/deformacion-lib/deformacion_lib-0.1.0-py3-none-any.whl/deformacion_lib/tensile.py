import cv2
import glob
import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import shutil
import imageio.v2 as imageio


def extract_frames(video_path, n_frames, ext, frames_out):
    """Extrae n_frames equiespaciados de un video."""
    if os.path.exists(frames_out):
        shutil.rmtree(frames_out)
    os.makedirs(frames_out)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"No se puede abrir el video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        raise ValueError("Conteo de frames inválido")

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


def crop_images(image_pattern, output_dir):
    """Recorta todas las imágenes usando un ROI definido por el usuario."""
    image_paths = sorted(glob.glob(image_pattern))
    if len(image_paths) == 0:
        raise RuntimeError(f"No se encontraron imágenes: {image_pattern}")

    img0 = cv2.imread(image_paths[0])
    if img0 is None:
        raise RuntimeError("Error al leer la primera imagen")

    cv2.namedWindow("Select ROI", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Select ROI", 1000, 800)
    x, y, w, h = cv2.selectROI("Select ROI", img0, showCrosshair=True)
    cv2.destroyAllWindows()

    os.makedirs(output_dir, exist_ok=True)

    for i, path in enumerate(image_paths):
        img = cv2.imread(path)
        if img is None:
            continue
        roi = img[y:y+h, x:x+w]
        cv2.imwrite(os.path.join(output_dir, f"crop_{i:04d}.tif"), roi)

    print(f"✅ {len(image_paths)} imágenes recortadas")


def medir_distancia_en_imagen(gray_image, thresh_value=80, min_black_fraction=0.7):
    """
    Detecta dos líneas horizontales negras y devuelve:
    distancia en píxeles, y_top, y_bottom
    """
    if gray_image is None or len(gray_image.shape) != 2:
        raise ValueError("Imagen en escala de grises inválida")

    _, binary = cv2.threshold(gray_image, thresh_value, 255, cv2.THRESH_BINARY_INV)
    mask = binary > 0
    row_counts = mask.sum(axis=1)

    height, width = gray_image.shape
    min_black_pixels = min_black_fraction * width

    rows = np.where(row_counts > min_black_pixels)[0]
    if rows.size == 0:
        raise RuntimeError("No se detectaron líneas negras válidas")

    y_top = int(rows[0])
    y_bottom = int(rows[-1])
    distance_px = int(y_bottom - y_top)

    return distance_px, y_top, y_bottom


def calcular_strain_y_elongacion(cropped_dir, total_time, L0_mm):
    """Calcula strain y elongación desde imágenes recortadas."""
    image_paths = sorted(glob.glob(os.path.join(cropped_dir, "*.tif")))
    if len(image_paths) == 0:
        raise RuntimeError("No se encontraron imágenes recortadas")

    distances_px = []
    for path in image_paths:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        d_px, _, _ = medir_distancia_en_imagen(img)
        distances_px.append(d_px)

    distances_px = np.array(distances_px)
    L0_px = distances_px[0]
    mm_per_px = L0_mm / L0_px

    lengths_mm = distances_px * mm_per_px
    elongation_mm = lengths_mm - L0_mm
    strain = elongation_mm / L0_mm
    time = np.linspace(0, total_time, len(strain))

    return time, strain, elongation_mm, lengths_mm, mm_per_px


def crear_frames_con_lineas(cropped_dir, output_dir):
    """Dibuja las líneas detectadas sobre cada frame y guarda las imágenes."""
    image_paths = sorted(glob.glob(os.path.join(cropped_dir, "*.tif")))
    if len(image_paths) == 0:
        raise RuntimeError("No hay imágenes recortadas")

    os.makedirs(output_dir, exist_ok=True)

    for i, path in enumerate(image_paths):
        img_gray = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img_gray is None:
            continue

        d_px, y_top, y_bottom = medir_distancia_en_imagen(img_gray)
        img_bgr = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)
        width = img_bgr.shape[1]
        
        cv2.line(img_bgr, (0, y_top), (width, y_top), (0, 0, 255), 2)
        cv2.line(img_bgr, (0, y_bottom), (width, y_bottom), (255, 0, 0), 2)
        
        cv2.imwrite(os.path.join(output_dir, f"lined_{i:04d}.png"), img_bgr)

    print(f"✅ {len(image_paths)} frames con líneas guardados")


def crear_gif_frames_con_lineas(raw_processing_dir, output_path, duracion_total=2.0):
    """Crea un GIF a partir de los frames con líneas dibujadas."""
    image_paths = sorted(glob.glob(os.path.join(raw_processing_dir, "*.png")))
    if len(image_paths) == 0:
        raise RuntimeError("No hay frames procesados para crear GIF")

    frames = []
    for path in image_paths:
        img = cv2.imread(path)
        if img is not None:
            frames.append(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    duration = duracion_total / len(frames)
    imageio.mimsave(output_path, frames, duration=duration)
    print(f"✅ GIF creado: {output_path}")


def crear_gif_lineas_digitales(cropped_dir, output_path, L0_mm, mm_per_px, duracion_total=2.0):
    """
    Crea un GIF con fondo negro mostrando solo las líneas.
    """
    image_paths = sorted(glob.glob(os.path.join(cropped_dir, "*.tif")))
    if len(image_paths) == 0:
        raise RuntimeError("No hay imágenes para crear GIF digital")

    first_img = cv2.imread(image_paths[0], cv2.IMREAD_GRAYSCALE)
    if first_img is None:
        raise RuntimeError("No se pudo leer la primera imagen")
    
    height, width = first_img.shape
    frames = []

    for path in image_paths:
        img_gray = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img_gray is None:
            continue

        d_px, y_top, y_bottom = medir_distancia_en_imagen(img_gray)
        d_mm = d_px * mm_per_px

        canvas = np.zeros((height, width, 3), dtype=np.uint8)

        cv2.line(canvas, (0, y_top), (width, y_top), (0, 0, 255), 2)
        cv2.line(canvas, (0, y_bottom), (width, y_bottom), (255, 0, 0), 2)
        
        x_center = width // 2
        cv2.line(canvas, (x_center, y_top), (x_center, y_bottom), (0, 255, 255), 2)

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        text = f"{d_mm:.2f} mm"
        
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        text_img = np.zeros((text_size[1] + 10, text_size[0] + 10, 3), dtype=np.uint8)
        cv2.putText(text_img, text, (5, text_size[1] + 2), font, font_scale, (255, 255, 255), thickness)
        
        text_rotated = cv2.rotate(text_img, cv2.ROTATE_90_CLOCKWISE)
        
        th, tw = text_rotated.shape[:2]
        y_center = (y_top + y_bottom) // 2
        text_y_start = max(0, y_center - th // 2)
        text_y_end = min(height, text_y_start + th)
        text_x_start = min(width - tw, x_center + 15)
        text_x_end = min(width, text_x_start + tw)
        
        th_actual = text_y_end - text_y_start
        tw_actual = text_x_end - text_x_start
        if th_actual > 0 and tw_actual > 0:
            text_crop = text_rotated[:th_actual, :tw_actual]
            mask = text_crop.any(axis=2)
            canvas[text_y_start:text_y_end, text_x_start:text_x_end][mask] = text_crop[mask]

        frames.append(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))

    duration = duracion_total / len(frames)
    imageio.mimsave(output_path, frames, duration=duration)
    print(f"✅ GIF digital creado: {output_path}")


def guardar_graficas_separadas(time_data, strain_data, elongation_data, output_dir):
    """Guarda strain vs time y elongation vs time en archivos separados."""
    os.makedirs(output_dir, exist_ok=True)

    fig1, ax1 = plt.subplots(figsize=(8, 6))
    ax1.plot(time_data, strain_data, 'b-', linewidth=2)
    ax1.set_title("Strain vs Time", fontsize=14, fontweight='bold')
    ax1.set_xlabel("Time [s]", fontsize=12)
    ax1.set_ylabel("Strain [-]", fontsize=12)
    ax1.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "strain_vs_time.png"), dpi=200)
    plt.close()

    fig2, ax2 = plt.subplots(figsize=(8, 6))
    ax2.plot(time_data, elongation_data, 'r-', linewidth=2)
    ax2.set_title("Elongation vs Time", fontsize=14, fontweight='bold')
    ax2.set_xlabel("Time [s]", fontsize=12)
    ax2.set_ylabel("Elongation [mm]", fontsize=12)
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "elongation_vs_time.png"), dpi=200)
    plt.close()

    print(f"✅ Gráficas guardadas en: {output_dir}")


def ejecutar_analisis_tensile(
    modo,
    nombre_archivo,
    tiempo_experimento,
    L0_mm,
    n_frames=None,
    ext_imagen=".tif",
    base_dir=None,
    duracion_gifs=2.0
):
    """
    Función principal que ejecuta todo el análisis del ensayo de tracción.
    
    Parámetros:
    modo: "video" o "foto"
    nombre_archivo: nombre del video o carpeta de imágenes
    tiempo_experimento: duración total del experimento en segundos
    L0_mm: longitud inicial entre las dos líneas en milímetros
    n_frames: número de frames a extraer (solo para modo video)
    ext_imagen: extensión de las imágenes (default: ".tif")
    base_dir: directorio base (default: directorio actual)
    duracion_gifs: duración de los GIFs en segundos (default: 2.0)
    """
    if base_dir is None:
        base_dir = os.getcwd()

    FRAMES_DIR = os.path.join(base_dir, "ExtractedFrames")
    CROPPED_DIR = os.path.join(base_dir, "CroppedImages")

    RESULTS_DIR = os.path.join(base_dir, "Results (Tensile Test Program)")
    ANALYSIS_DIR = os.path.join(RESULTS_DIR, "analysis")
    RAW_PROCESSING_DIR = os.path.join(RESULTS_DIR, "raw_processing")
    VISUAL_DIR = os.path.join(RESULTS_DIR, "visual")

    os.makedirs(ANALYSIS_DIR, exist_ok=True)
    os.makedirs(RAW_PROCESSING_DIR, exist_ok=True)
    os.makedirs(VISUAL_DIR, exist_ok=True)

    if modo.lower() == "video":
        if n_frames is None:
            raise ValueError("Debes especificar n_frames para modo video")
        
        video_path = os.path.join(base_dir, nombre_archivo)
        print(f"\n🎹 Extrayendo {n_frames} frames del video...")
        extract_frames(video_path, n_frames, ext_imagen, FRAMES_DIR)
        frames_dir = FRAMES_DIR
    else:
        frames_dir = os.path.join(base_dir, nombre_archivo)
        print(f"\n📁 Usando imágenes de: {frames_dir}")

    print("\n✂️ Selecciona el ROI en la primera imagen...")
    crop_images(os.path.join(frames_dir, f"*{ext_imagen}"), CROPPED_DIR)

    print("\n📊 Calculando strain y elongación...")
    time_data, strain_data, elongation_data, lengths_mm, mm_per_px = \
        calcular_strain_y_elongacion(CROPPED_DIR, tiempo_experimento, L0_mm)

    print("\n💾 Guardando resultados en CSV...")
    csv_path = os.path.join(ANALYSIS_DIR, "results_tensile.csv")
    pd.DataFrame({
        "time_s": time_data,
        "strain": strain_data,
        "elongation_mm": elongation_data,
        "length_mm": lengths_mm
    }).to_csv(csv_path, index=False)
    print(f"✅ CSV guardado: {csv_path}")

    print("\n🎨 Creando frames con líneas...")
    crear_frames_con_lineas(CROPPED_DIR, RAW_PROCESSING_DIR)

    print("\n🎬 Creando GIF de frames con líneas...")
    gif_frames_path = os.path.join(VISUAL_DIR, "frames_with_lines.gif")
    crear_gif_frames_con_lineas(RAW_PROCESSING_DIR, gif_frames_path, duracion_gifs)

    print("\n🎬 Creando GIF digital (solo líneas)...")
    gif_digital_path = os.path.join(VISUAL_DIR, "digital_lines.gif")
    crear_gif_lineas_digitales(CROPPED_DIR, gif_digital_path, L0_mm, mm_per_px, duracion_gifs)

    print("\n📈 Guardando gráficas...")
    guardar_graficas_separadas(time_data, strain_data, elongation_data, ANALYSIS_DIR)

    print("\n🗑️ Limpiando archivos temporales...")
    if os.path.exists(FRAMES_DIR):
        shutil.rmtree(FRAMES_DIR)
    if os.path.exists(CROPPED_DIR):
        shutil.rmtree(CROPPED_DIR)
    print("✅ Carpetas temporales eliminadas")

    print("\n" + "="*60)
    print("✅ ANÁLISIS COMPLETADO EXITOSAMENTE")
    print("="*60)
    print(f"📂 Resultados guardados en: {RESULTS_DIR}")
    print(f"   ├─ analysis/          (gráficas strain y elongation)")
    print(f"   ├─ raw_processing/    (frames con líneas)")
    print(f"   └─ visual/            (GIFs)")
    print("="*60 + "\n")