from __future__ import annotations


def the_mason_vectorize(image_path: str, color_count: int = 8, smoothness: float = 0.01) -> str:
    """Translates a raster image into a set of smooth SVG color blobs."""
    try:
        import cv2
        import numpy as np
        from sklearn.cluster import KMeans
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Missing dependencies for Mason vectorization. Install opencv-python, numpy, and scikit-learn."
        ) from exc

    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not load image at path: {image_path}")

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w, _ = img_rgb.shape

    pixels = img_rgb.reshape(-1, 3)
    kmeans = KMeans(n_clusters=color_count, n_init=10).fit(pixels)
    quantized_img = kmeans.cluster_centers_[kmeans.labels_].reshape(h, w, 3).astype("uint8")

    svg_paths: list[str] = []

    for color in kmeans.cluster_centers_:
        lower = np.array(color - 1, dtype="uint8")
        upper = np.array(color + 1, dtype="uint8")
        mask = cv2.inRange(quantized_img, lower, upper)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)
        hex_color = "#{:02x}{:02x}{:02x}".format(int(color[0]), int(color[1]), int(color[2]))

        for cnt in contours:
            if cv2.contourArea(cnt) < 20:
                continue

            epsilon = smoothness * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)

            path_data = "M " + " L ".join([f"{p[0][0]},{p[0][1]}" for p in approx]) + " Z"
            svg_paths.append(
                f'<path d="{path_data}" fill="{hex_color}" stroke="{hex_color}" stroke-width="1"/>'
            )

    svg_output = (
        f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
        + "".join(svg_paths)
        + "</svg>"
    )
    return svg_output
