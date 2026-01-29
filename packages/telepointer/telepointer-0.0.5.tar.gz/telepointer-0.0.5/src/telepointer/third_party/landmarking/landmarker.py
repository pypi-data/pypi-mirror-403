# Copyright 2023 The MediaPipe Authors. All Rights Reserved.
# @title Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# THIS FILE IS LOOSELY DERIVED FROM THE EXAMPLE CODE PROVIDED
# BY THE MEDIAPIPE AUTHORS AND CONTAINS SIGNIFICANT CHANGES.
# THESE CHANGES ARE Copyright 2025 Jeremy Dufour

from telepointer.landmarking.landmarker import Landmarker
import mediapipe as mp
import time
from mediapipe.tasks.python import vision
import cv2 as cv
import numpy as np
import logging
import os


def get_score(category):
    return category.score


class BlazeFaceLandmarker(Landmarker):
    def _create_landmarker(self, callback):
        if not os.environ.get("TELEPOINTER_MEDIAPIPE_LANDMARKER_PATH"):
            raise Exception("TELEPOINTER_MEDIAPIPE_LANDMARKER_PATH not set. Please set it to the path of the face_landmarker.task model bundle downloadable at https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker.")

        def output_result(result, image, timestamp):
            if len(result.facial_transformation_matrixes) and len(
                result.face_blendshapes
            ):
                face_transform_matrix = result.facial_transformation_matrixes[0]

                face_blendshapes = [
                    category.score for category in result.face_blendshapes[0]
                ]

                callback(face_transform_matrix, face_blendshapes, timestamp)

        options = vision.FaceLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path=os.environ.get("TELEPOINTER_MEDIAPIPE_LANDMARKER_PATH")
            ),
            running_mode=vision.RunningMode.LIVE_STREAM,
            output_facial_transformation_matrixes=True,
            output_face_blendshapes=True,
            result_callback=output_result,
        )

        try:
            return vision.FaceLandmarker.create_from_options(options)
        except:
            raise Exception("Could not create BlazeFaceLandmarker. TELEPOINTER_MEDIAPIPE_LANDMARKER_PATH may not be pointing to the right file.")

    def _run_async(self, landmarker, raw_frame, timestamp):
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=raw_frame)
        landmarker.detect_async(mp_image, timestamp)

