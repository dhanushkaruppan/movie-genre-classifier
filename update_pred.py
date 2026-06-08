import json
import sys

with open('c:/Users/dhanu/OneDrive/Documents/antigravity_dev/movie_genre_classification/prediction.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find the cell to replace
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code' and len(cell['source']) > 0 and '# ---------- Single‑image prediction helper ----------\n' in cell['source'][0]:
        break
else:
    print('Cell not found!')
    sys.exit(1)

new_source = '''import io
from PIL import Image as PILImg
from google.colab import files

# ── Load model & class names ──────────────────────────────────
MODEL_PATH = os.path.join(SAVE_DIR, 'movie_poster_classifier_v2_final.keras')
NAMES_PATH = os.path.join(SAVE_DIR, 'class_names.json')

loaded_model = tf.keras.models.load_model(
    MODEL_PATH,
    custom_objects={'WarmUpCosineDecay': WarmUpCosineDecay}
)
with open(NAMES_PATH) as f:
    loaded_class_names = json.load(f)

print(f"Model loaded from: {MODEL_PATH}")
print(f"Classes: {loaded_class_names}")

# ── TTA augmentations ─────────────────────────────────────────
TTA_AUGS = [
    lambda x: x,                                        # original
    lambda x: tf.image.flip_left_right(x),              # h-flip
    lambda x: tf.image.adjust_brightness(x, 0.1),       # brighter
    lambda x: tf.image.adjust_brightness(x, -0.1),      # darker
    lambda x: tf.image.central_crop(x, 0.9),            # slight crop
]

def resize_fn(img, size=IMG_SIZE):
    return tf.image.resize(img, size)

def predict_with_tta(model, img_array_raw, n_augs=5):
    """
    img_array_raw: numpy array, shape (H, W, 3), dtype uint8, values 0-255
    Returns averaged probability vector.
    """
    img_tensor = tf.cast(img_array_raw, tf.float32)
    all_probs  = []

    augs_to_use = TTA_AUGS[:n_augs]
    for aug_fn in augs_to_use:
        augmented = aug_fn(img_tensor)
        resized   = resize_fn(augmented)
        # IMPORTANT: use the exact same preprocessing as training
        preprocessed = tf.keras.applications.efficientnet_v2.preprocess_input(resized)
        batch = tf.expand_dims(preprocessed, 0)
        probs = model.predict(batch, verbose=0)[0]
        all_probs.append(probs)

    averaged = np.mean(all_probs, axis=0)
    return averaged

# ── Upload & predict ──────────────────────────────────────────
print("\\nPlease upload one or more movie poster images …")
uploaded = files.upload()

if not uploaded:
    print("No files uploaded.")
else:
    for filename, content in uploaded.items():
        print(f"\\n{'='*55}")
        print(f"  File: {filename}")
        print(f"{'='*55}")

        try:
            pil_img = PILImg.open(io.BytesIO(content)).convert('RGB')
            img_np  = np.array(pil_img)                      # (H, W, 3) uint8

            # TTA prediction
            avg_probs = predict_with_tta(loaded_model, img_np, n_augs=5)
            top_idx   = int(np.argmax(avg_probs))
            top_label = loaded_class_names[top_idx]
            top_conf  = float(avg_probs[top_idx])

            # Display image + results
            fig, (ax_img, ax_bar) = plt.subplots(1, 2, figsize=(12, 5))

            ax_img.imshow(pil_img)
            ax_img.set_title(f"Predicted: {top_label}  ({top_conf:.1%} confidence)",
                             fontsize=13, fontweight='bold',
                             color='green' if top_conf > 0.5 else 'orange')
            ax_img.axis('off')

            sorted_idx  = np.argsort(avg_probs)[::-1]
            sorted_probs = avg_probs[sorted_idx]
            sorted_names = [loaded_class_names[i] for i in sorted_idx]
            colors = ['#2ecc71' if i == 0 else '#3498db' for i in range(len(sorted_names))]

            bars = ax_bar.barh(sorted_names[::-1], sorted_probs[::-1], color=colors[::-1])
            ax_bar.set_xlim(0, 1)
            ax_bar.set_xlabel('Confidence (TTA averaged)', fontsize=11)
            ax_bar.set_title('Genre Probability Distribution', fontsize=12, fontweight='bold')
            for bar, prob in zip(bars, sorted_probs[::-1]):
                ax_bar.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                            f'{prob:.1%}', va='center', fontsize=9)
            ax_bar.grid(axis='x', alpha=0.3)

            plt.suptitle(f'{filename}', fontsize=10, color='gray')
            plt.tight_layout()
            plt.show()

            print(f"  Top prediction : {top_label}  ({top_conf:.1%})")
            print("  Full distribution (TTA):")
            for i in sorted_idx:
                bar = '█' * int(avg_probs[i] * 30)
                print(f"    {loaded_class_names[i]:<12s}: {avg_probs[i]:.4f}  {bar}")

        except Exception as e:
            print(f"  [ERROR] Failed to process {filename}: {e}")
'''

nb['cells'][i]['source'] = [line + '\n' for line in new_source.split('\n')]
if nb['cells'][i]['source']:
    nb['cells'][i]['source'][-1] = nb['cells'][i]['source'][-1].rstrip('\n')

with open('c:/Users/dhanu/OneDrive/Documents/antigravity_dev/movie_genre_classification/prediction.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print('Updated prediction.ipynb!')
