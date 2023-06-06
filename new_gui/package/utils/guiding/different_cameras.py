from package.utils.cameras.zwo_camera import ZwoCamera, asi_initialized


def get_possible_cameras(vendor):
    if vendor == "ZWO":
        if not asi_initialized:
            ZwoCamera.initialize_library()
        return ZwoCamera.get_cameras_list()
