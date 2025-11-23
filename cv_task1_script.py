import bpy
import os
import random
import math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

OUTPUT_DIR = r"/Users/reemeldalil/Desktop/cv_1_dataset"
NUM_IMAGES = 50
IMG_RES = 1024
CLASS_ID = 0
OBJECT_NAME = "Table"
CAMERA_NAME = "Camera"
MOVE_RADIUS = 5
MAX_ROT = math.radians(15)

def ensure_dir(p):
    if not os.path.exists(p):
        os.makedirs(p)

def world_bbox(obj):
    return [obj.matrix_world @ Vector(c) for c in obj.bound_box]

def yolo_bbox(obj, cam, scene):
    pts = [world_to_camera_view(scene, cam, p) for p in world_bbox(obj)]
    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]

    if all(z < 0 for z in zs):  # behind camera
        return None

    min_x = max(0, min(xs)); max_x = min(1, max(xs))
    min_y = max(0, min(ys)); max_y = min(1, max(ys))
    if max_x <= min_x or max_y <= min_y:
        return None

    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    w = max_x - min_x
    h = max_y - min_y
    return cx, cy, w, h

def main():
    images = os.path.join(OUTPUT_DIR, "images")
    labels = os.path.join(OUTPUT_DIR, "labels")
    ensure_dir(images); ensure_dir(labels)

    scene = bpy.context.scene
    obj = bpy.data.objects[OBJECT_NAME]
    cam = bpy.data.objects[CAMERA_NAME]
    scene.camera = cam

    # render settings
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 32
    scene.render.resolution_x = IMG_RES
    scene.render.resolution_y = IMG_RES

    for i in range(NUM_IMAGES):

        # ---- RANDOM MOVEMENT ----
        angle = random.random() * math.tau
        r = random.random() * MOVE_RADIUS
        obj.location.x = math.cos(angle) * r
        obj.location.y = math.sin(angle) * r

        # ---- RANDOM ROTATION ----
        obj.rotation_euler.z = random.uniform(-MAX_ROT, MAX_ROT)
        bpy.context.view_layer.update()

        # ---- YOLO BOUNDING BOX ----
        bb = yolo_bbox(obj, cam, scene)
        if bb is None:
            print(f"Object invisible at frame {i}, skipping...")
            continue

        cx, cy, w, h = bb
        label = f"{CLASS_ID} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n"

        # ---- RENDER ----
        img_name = f"img_{i:04d}.png"
        scene.render.filepath = os.path.join(images, img_name)
        bpy.ops.render.render(write_still=True)

        # ---- SAVE LABEL ----
        with open(os.path.join(labels, f"img_{i:04d}.txt"), "w") as f:
            f.write(label)

        print("Saved", img_name)

    print("DONE")

main()
