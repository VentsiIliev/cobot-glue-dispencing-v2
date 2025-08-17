import os

from pl_gui.Endpoints import SAVE_WORKPIECE, CREATE_WORKPIECE_TOPIC


class CreateWorkpieceManager:


    def __init__(self, contour_editor,controller):
        self.contour_editor = contour_editor
        self.controller = controller

    def via_camera(self):
        self.controller.handle(CREATE_WORKPIECE_TOPIC,
                               self.via_camera_success,
                               self.via_camera_failure)

    def via_dxf(self):
        pass

    def via_camera_on_create_workpiece_submit(self,data):
        wp_contours_data = self.contour_editor.to_wp_data()
        sprayPatternsDict = {
            "Contour": [],
            "Fill": []
        }
        sprayPatternsDict['Contour'] = wp_contours_data.get('Contour')
        sprayPatternsDict['Fill'] = wp_contours_data.get('Fill')

        from API.shared.workpiece.Workpiece import WorkpieceField

        data[WorkpieceField.SPRAY_PATTERN.value] = sprayPatternsDict
        data[WorkpieceField.CONTOUR.value] = wp_contours_data.get('External')
        self.controller.handle(SAVE_WORKPIECE, data)

    def via_camera_success(self,frame,contours,data):
        self.contour_editor.set_image(frame)
        contours_by_layer = {
            "External": [contours] if len(contours) > 0 else [],
            "Contour": [],
            "Fill": []
        }

        self.contour_editor.init_contours(contours_by_layer)
        self.contour_editor.set_create_workpiece_for_on_submit_callback(self.via_camera_on_create_workpiece_submit)

    def via_camera_failure(self, req, msg):
        from pl_gui.FeedbackProvider import FeedbackProvider
        FeedbackProvider.showMessage(msg)

