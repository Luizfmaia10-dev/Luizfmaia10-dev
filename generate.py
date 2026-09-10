import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import math

# ============================================================
# CONFIGURAÇÕES
# ============================================================

INPUT = "assets/luiz.jpg"
OUTPUT = "assets/animation/luiz_drawing.gif"

WIDTH = 700
HEIGHT = 700

FPS = 20

# Duração aproximada
MACHINE_FRAMES = 20
DRAW_FRAMES = 110
DETAIL_FRAMES = 35
COLOR_FRAMES = 35
SIGNATURE_FRAMES = 35

BG = (248, 249, 252)
INK = (35, 35, 42)
BLUE = (65, 74, 250)


# ============================================================
# PASTAS
# ============================================================

os.makedirs("assets/animation", exist_ok=True)


# ============================================================
# CARREGAR FOTO
# ============================================================

image = cv2.imread(INPUT)

if image is None:
    raise FileNotFoundError(
        f"Não encontrei a imagem em: {INPUT}"
    )

print("Foto carregada!")


# ============================================================
# REDIMENSIONAR MANTENDO PROPORÇÃO
# ============================================================

h, w = image.shape[:2]

scale = min(
    (WIDTH - 100) / w,
    (HEIGHT - 100) / h
)

new_w = int(w * scale)
new_h = int(h * scale)

image = cv2.resize(
    image,
    (new_w, new_h),
    interpolation=cv2.INTER_AREA
)


# ============================================================
# CANVAS
# ============================================================

canvas = np.full(
    (HEIGHT, WIDTH, 3),
    255,
    dtype=np.uint8
)

x = (WIDTH - new_w) // 2
y = (HEIGHT - new_h) // 2

canvas[
    y:y + new_h,
    x:x + new_w
] = image


# ============================================================
# FOTO RGB
# ============================================================

original_rgb = cv2.cvtColor(
    canvas,
    cv2.COLOR_BGR2RGB
)


# ============================================================
# PROCESSAMENTO DOS CONTORNOS
# ============================================================

gray = cv2.cvtColor(
    canvas,
    cv2.COLOR_BGR2GRAY
)

gray = cv2.GaussianBlur(
    gray,
    (5, 5),
    0
)

edges = cv2.Canny(
    gray,
    40,
    130
)


# ============================================================
# REMOVER PEQUENOS RUÍDOS
# ============================================================

contours, _ = cv2.findContours(
    edges,
    cv2.RETR_LIST,
    cv2.CHAIN_APPROX_NONE
)

# Remover contornos muito pequenos
contours = [
    c for c in contours
    if cv2.arcLength(c, False) > 25
]


# ============================================================
# ORDENAR OS TRAÇOS
# ============================================================

contours = sorted(
    contours,
    key=lambda c: (
        cv2.boundingRect(c)[1],
        cv2.boundingRect(c)[0]
    )
)

print(f"Traços encontrados: {len(contours)}")


# ============================================================
# CONVERTER CONTORNOS PARA PONTOS
# ============================================================

paths = []

for contour in contours:

    points = contour.reshape(-1, 2)

    if len(points) < 2:
        continue

    paths.append(points)


# ============================================================
# FONTES
# ============================================================

try:
    font = ImageFont.truetype(
        "arial.ttf",
        20
    )
except:
    font = ImageFont.load_default()


# ============================================================
# FUNÇÃO: DESENHAR MÁQUINA
# ============================================================

def draw_machine(frame, progress):

    img = Image.fromarray(frame)

    draw = ImageDraw.Draw(img)

    # Área da máquina
    machine_y = 40

    # Movimento horizontal
    machine_x = int(
        80 + progress * (WIDTH - 160)
    )

    # Trilho
    draw.line(
        (50, machine_y, WIDTH - 50, machine_y),
        fill=(180, 183, 195),
        width=5
    )

    # Cabeça da máquina
    draw.rounded_rectangle(
        (
            machine_x - 35,
            machine_y - 12,
            machine_x + 35,
            machine_y + 25
        ),
        radius=8,
        fill=(55, 58, 70),
        outline=(20, 20, 25),
        width=2
    )

    # Haste
    draw.line(
        (
            machine_x,
            machine_y + 25,
            machine_x,
            machine_y + 70
        ),
        fill=(70, 72, 82),
        width=4
    )

    # Caneta
    draw.polygon(
        [
            (machine_x - 7, machine_y + 65),
            (machine_x + 7, machine_y + 65),
            (machine_x, machine_y + 82)
        ],
        fill=BLUE
    )

    return np.array(img)


# ============================================================
# FUNÇÃO: FUNDO
# ============================================================

def blank():

    return np.full(
        (HEIGHT, WIDTH, 3),
        255,
        dtype=np.uint8
    )


# ============================================================
# FRAMES
# ============================================================

frames = []


# ============================================================
# 1 — MÁQUINA ENTRANDO
# ============================================================

print("1/5 Máquina entrando...")

for i in range(MACHINE_FRAMES):

    progress = i / (MACHINE_FRAMES - 1)

    frame = blank()

    frame = draw_machine(
        frame,
        progress
    )

    frames.append(
        Image.fromarray(frame)
    )


# ============================================================
# 2 — DESENHO DOS TRAÇOS
# ============================================================

print("2/5 Desenhando traços...")


drawing = blank()

total_paths = len(paths)

for frame_number in range(DRAW_FRAMES):

    progress = (
        frame_number + 1
    ) / DRAW_FRAMES

    visible = max(
        1,
        int(total_paths * progress)
    )

    frame = drawing.copy()

    # Desenhar os caminhos progressivamente
    for path in paths[:visible]:

        cv2.polylines(
            frame,
            [path.reshape(-1, 1, 2)],
            False,
            INK,
            1,
            cv2.LINE_AA
        )

    # Máquina se movimentando
    machine_progress = (
        frame_number / max(1, DRAW_FRAMES - 1)
    )

    frame = draw_machine(
        frame,
        machine_progress
    )

    frames.append(
        Image.fromarray(frame)
    )

    drawing = frame.copy()


# ============================================================
# 3 — DETALHES
# ============================================================

print("3/5 Adicionando detalhes...")


for i in range(DETAIL_FRAMES):

    progress = (
        i + 1
    ) / DETAIL_FRAMES

    frame = drawing.copy()

    # Pequenas linhas adicionais
    threshold = int(
        len(paths) * (
            0.85 + 0.15 * progress
        )
    )

    for path in paths[:threshold]:

        cv2.polylines(
            frame,
            [path.reshape(-1, 1, 2)],
            False,
            INK,
            1,
            cv2.LINE_AA
        )

    frames.append(
        Image.fromarray(frame)
    )


# ============================================================
# 4 — REVELAR CORES
# ============================================================

print("4/5 Revelando cores...")


for i in range(COLOR_FRAMES):

    progress = (
        i + 1
    ) / COLOR_FRAMES

    # Suavização
    smooth = (
        progress
        * progress
        * (3 - 2 * progress)
    )

    # Máscara vertical + horizontal
    yy, xx = np.mgrid[
        0:HEIGHT,
        0:WIDTH
    ]

    center_x = WIDTH / 2
    center_y = HEIGHT / 2

    distance = np.sqrt(
        ((xx - center_x) / WIDTH) ** 2 +
        ((yy - center_y) / HEIGHT) ** 2
    )

    mask = smooth - distance * 0.25

    mask = np.clip(
        mask,
        0,
        1
    )

    mask = mask[..., np.newaxis]

    frame_float = drawing.astype(
        np.float32
    )

    photo_float = original_rgb.astype(
        np.float32
    )

    result = (
        frame_float * (1 - mask)
        +
        photo_float * mask
    )

    result = np.clip(
        result,
        0,
        255
    ).astype(np.uint8)

    frames.append(
        Image.fromarray(result)
    )


# ============================================================
# 5 — ASSINATURA
# ============================================================

print("5/5 Finalizando...")


final_image = Image.fromarray(
    original_rgb
)

for i in range(SIGNATURE_FRAMES):

    progress = (
        i + 1
    ) / SIGNATURE_FRAMES

    img = final_image.copy()

    draw = ImageDraw.Draw(img)

    # Linha de assinatura
    start_x = 470
    start_y = 630

    end_x = int(
        start_x + 130 * progress
    )

    draw.line(
        (
            start_x,
            start_y,
            end_x,
            start_y
        ),
        fill=BLUE,
        width=3
    )

    # Nome
    if progress > 0.35:

        alpha = min(
            1,
            (progress - 0.35) / 0.65
        )

        text = "Luiz Fernando Maia"

        draw.text(
            (
                470,
                645
            ),
            text,
            fill=(
                int(65 * alpha),
                int(74 * alpha),
                int(250 * alpha)
            ),
            font=font
        )

    frames.append(img)


# ============================================================
# SEGURANÇA — ÚLTIMO FRAME
# ============================================================

frames.append(
    Image.fromarray(original_rgb)
)


# ============================================================
# SALVAR GIF
# ============================================================

print("Salvando GIF...")

frames[0].save(
    OUTPUT,
    save_all=True,
    append_images=frames[1:],
    duration=int(1000 / FPS),
    loop=0,
    optimize=False
)


# ============================================================
# RESULTADO
# ============================================================

print()
print("==============================================")
print("       ANIMAÇÃO PREMIUM GERADA!")
print("==============================================")
print()
print(f"Arquivo: {OUTPUT}")
print(f"Frames: {len(frames)}")
print(f"Resolução: {WIDTH}x{HEIGHT}")
print()

