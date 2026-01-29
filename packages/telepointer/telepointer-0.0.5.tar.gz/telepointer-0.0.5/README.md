# Telepointer
![PyPI - Version](https://img.shields.io/pypi/v/telepointer)

Ever wanted to use your head to move the mouse cursor around? Now you can, with Telepointer!

# Usage

> [!IMPORTANT]
> Telepointer requires the face_landmarker.task model bundle downloadable at https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker . 
> The telepointer_MEDIAPIPE_LANDMARKER_PATH environment variable must point to the location of face_landmarker.task.

Telepointer has two components: the `telepointer` mouse controller and the `tpctrl` command-line tool.

## telepointer

This is the main program in charge of translating your head movements into mouse movements.
This functionality may, however, not always be needed. Therefore, this program is equipped with the ability to receive various commands to enable or disable
mouse control among other things. These commands may be sent via terminal or optionally by socket as well by using the `-s` flag.
This is where `tpctrl` comes into play.

## tpctrl

This a command line tool to send commands to the main `telepointer` program via socket. 
It is not meant for direct use by humans but as an interface for other software, like hotkey software, to control `telepointer`.
You can find examples of hotkey scripts for [sxhkd](https://github.com/baskerville/sxhkd) and [AutoHotkey](https://www.autohotkey.com/) in the `examples/` directory.

The available commands are:

`tpctrl start`
Start controlling the cursor

`tpctrl stop`
Stop controlling the cursor

`tpctrl calibrate`
Triggers calibration for the current landmarker processor.
The behaviour of this command depends on the landmarker processor.
With the default processor, (i.e. `TrackballLandmarkerProcessor`), this will reset the cursor to the center of the screen.

`tpctrl click`
Triggers a left mouse click.

`tpctrl press`
Keeps the left mouse button down until `tpctrl lift` is called

`tpctrl lift`
Releases the left mouse button

`tpctrl quit`
Stops the execution of `telepointer`. While `tpctrl stop` will simply pause `telepointer` until `tpctrl start` is called, `tpctrl quit` will cause `telepointer` to exit entirely.



