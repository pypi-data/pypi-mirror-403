"""Utilities for rendering 3D data with VTK."""
import os.path
import importlib.metadata
import vtk
import numpy as np
import cardiacctexplorer.surface_utils as surfutils
from cardiacctexplorer.surface_utils import read_nifti_itk_to_vtk

class RenderTotalSegmentatorData:
    """
    Can render data from TotalsSegmentator.
    Can also dump rendering to an image file.

    This is a super class that should be inherited.
    """
    def __init__(self, win_size=(1600, 800), render_to_file=True):
        self.ren_win = vtk.vtkRenderWindow()
        self.ren_win.SetOffScreenRendering(render_to_file)
        self.win_size = win_size
        self.ren_win.SetSize(win_size)
        self.ren_win.SetWindowName("Explorer view")

        self.vtk_image = None
        self.ren_volume = None
        self.ren_text = None
        self.ren_patient_text = None
        self.ren_warning_text = None

        self.viewport_volume = [0.60, 0.0, 1.0, 1.0]
        self.iren = vtk.vtkRenderWindowInteractor()
        self.iren.SetRenderWindow(self.ren_win)
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.iren.SetInteractorStyle(style)

        self.actors = []
        self.landmarks = []
        self.centerlines = []

        # The text message that will be showed in the text renderer
        self.message_text = ""
        self.patient_text = ""
        self.warning_text = ""

    def render_interactive(self):
        """
        Creates an interactive renderwindow with the results
        """
        pos = (5, 5)
        font_size = 12
        self.add_text_to_render(
            self.ren_text,
            self.message_text,
            color=(1.0, 1.0, 1.0),
            position=pos,
            font_size=font_size,
        )
        self.add_text_to_render(
            self.ren_patient_text,
            self.patient_text,
            color=(0.0, 1.0, 0.0),
            position=pos,
            font_size=font_size,
        )
        self.add_text_to_render(
            self.ren_warning_text,
            self.warning_text,
            color=(1.0, 1.0, 0.0),
            position=pos,
            font_size=font_size,
        )
        self.iren.Start()

    def render_to_file(self, file_name):
        """
        Write the renderwindow to an image file
        :param file_name: Image file name (.png)
        """
        # viewport_size = self.ren_text.GetSize()
        # print(f"Viewport size {size}")
        # pos = (5, viewport_size[1] - 50)
        pos = (5, 5)
        self.add_text_to_render(
            self.ren_text, self.message_text, color=(1.0, 1.0, 1.0), position=pos
        )
        self.add_text_to_render(
            self.ren_patient_text,
            self.patient_text,
            color=(0.0, 1.0, 0.0),
            position=pos,
        )
        self.add_text_to_render(
            self.ren_warning_text,
            self.warning_text,
            color=(1.0, 1.0, 0.0),
            position=pos,
        )

        self.ren_win.SetOffScreenRendering(1)
        # print(f"Writing visualization to {file_name}")
        self.ren_win.SetSize(self.win_size)
        self.ren_win.Render()
        w2if = vtk.vtkWindowToImageFilter()
        w2if.SetInput(self.ren_win)
        writer_png = vtk.vtkPNGWriter()
        writer_png.SetInputConnection(w2if.GetOutputPort())
        writer_png.SetFileName(file_name)
        writer_png.Write()

    def set_sitk_image_file(self, input_file, img_mask=None):
        """
        Add a simple ITK image to the renderer using a volume renderer.
        If a mask is provided, the volume data is first masked. This can for example remove scanner beds etc.
        """
        self.vtk_image = read_nifti_itk_to_vtk(
            input_file, img_mask, flip_for_volume_rendering=True
        )
        if self.vtk_image is None:
            return

        vtk_dim = self.vtk_image.GetDimensions()
        vtk_spc = self.vtk_image.GetSpacing()

        img_txt = (f"Spacing: ({vtk_spc[0]:.2f}, {vtk_spc[1]:.2f}, {vtk_spc[2]:.2f}) mm"
                   f"\nDimensions: ({vtk_dim[0]}, {vtk_dim[1]}, {vtk_dim[2]}) vox\n"
                   f"Size: ({vtk_spc[0] * vtk_dim[0] / 10.0:.1f}, {vtk_spc[1] * vtk_dim[1] / 10.0:.1f}, {vtk_spc[2] * vtk_dim[2] / 10.0:.1f}) cm\n")
        self.message_text += img_txt

        # Get direction to set camera (not needed when we do the brutal flip of image data in the load routine)
        # dir_mat = self.vtk_image.GetDirectionMatrix().GetData()
        # print(f"Dir mat: {dir_mat}")
        # dir_val = dir_mat[4]
        dir_val = 1

        # Reset direction matrix, since volume render do not cope good with it
        direction = [1, 0, 0.0, 0, 1, 0.0, 0.0, 0.0, 1.0]
        self.vtk_image.SetDirectionMatrix(direction)

        volume_mapper = vtk.vtkSmartVolumeMapper()
        volume_mapper.SetInputData(self.vtk_image)
        volume = vtk.vtkVolume()
        volume.SetMapper(volume_mapper)

        self.ren_volume = vtk.vtkRenderer()
        self.ren_volume.SetViewport(self.viewport_volume)

        volume_color = vtk.vtkColorTransferFunction()
        volume_color.AddRGBPoint(-2048, 0.0, 0.0, 0.0)
        volume_color.AddRGBPoint(145, 0.0, 0.0, 0.0)
        volume_color.AddRGBPoint(145, 0.62, 0.0, 0.015)
        volume_color.AddRGBPoint(192, 0.91, 0.45, 0.0)
        volume_color.AddRGBPoint(217, 0.97, 0.81, 0.61)
        volume_color.AddRGBPoint(384, 0.91, 0.91, 1.0)
        volume_color.AddRGBPoint(478, 0.91, 0.91, 1.0)
        volume_color.AddRGBPoint(3660, 1, 1, 1.0)

        volume_scalar_opacity = vtk.vtkPiecewiseFunction()
        volume_scalar_opacity.AddPoint(-2048, 0.00)
        volume_scalar_opacity.AddPoint(143, 0.00)
        volume_scalar_opacity.AddPoint(145, 0.12)
        volume_scalar_opacity.AddPoint(192, 0.56)
        volume_scalar_opacity.AddPoint(217, 0.78)
        volume_scalar_opacity.AddPoint(385, 0.83)
        volume_scalar_opacity.AddPoint(3660, 0.83)

        volume_gradient_opacity = vtk.vtkPiecewiseFunction()
        volume_gradient_opacity.AddPoint(0, 1.0)
        volume_gradient_opacity.AddPoint(255, 1.0)

        volume_property = vtk.vtkVolumeProperty()
        volume_property.SetColor(volume_color)
        volume_property.SetScalarOpacity(volume_scalar_opacity)
        volume_property.SetGradientOpacity(volume_gradient_opacity)
        volume_property.SetInterpolationTypeToLinear()
        volume_property.ShadeOn()
        volume_property.SetAmbient(0.2)
        volume_property.SetDiffuse(1.0)
        volume_property.SetSpecular(0.0)

        volume.SetProperty(volume_property)
        self.ren_volume.AddViewProp(volume)

        self.ren_win.AddRenderer(self.ren_volume)

        c = volume.GetCenter()
        view_offsets = [500, 1000, 0]
        # Hack to handle direction matrices
        view_offsets[0] *= dir_val
        view_offsets[1] *= dir_val
        self.ren_volume.GetActiveCamera().SetParallelProjection(1)
        self.ren_volume.GetActiveCamera().SetViewUp(0, 0, 1)
        self.ren_volume.GetActiveCamera().SetPosition(
            c[0] + view_offsets[0], c[1] + view_offsets[1], c[2] + view_offsets[2]
        )
        self.ren_volume.GetActiveCamera().SetFocalPoint(c[0], c[1], c[2])
        # ren_volume.ResetCamera()
        self.ren_volume.ResetCameraScreenSpace()
        self.ren_volume.GetActiveCamera().Zoom(1.5)

    @staticmethod
    def add_text_to_render(
        ren, message, color=(1, 1, 1), position=(5, 5), font_size=10
    ):
        if ren is None or message is None or message == "":
            return
        txt = vtk.vtkTextActor()
        txt.SetInput(message)
        # txt.SetTextScaleModeToNone()
        # txt.SetTextScaleModeToViewport()
        txt.SetTextScaleModeToProp()
        txtprop = txt.GetTextProperty()
        # txtprop.SetFontFamilyToArial()
        # txtprop.SetFontSize(font_size)
        txtprop.SetColor(color)
        # txt.SetDisplayPosition(position[0], position[1])

        # txtprop.SetJustificationToLeft()
        txtprop.SetVerticalJustificationToTop()
        txt.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        # txt.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
        # txt.GetPositionCoordinate().SetValue(0.005, 0.99)
        txt.SetPosition(0.05, 0.05)
        txt.SetPosition2(0.95, 0.95)
        # txt.GetPositionCoordinate().SetValue(0.0, 0.0)
        # txt.GetPositionCoordinate2().SetValue(1.0, 1.0)
        # txt.SetTextScaleModeToViewport()
        ren.AddActor(txt)

    @staticmethod
    def generate_actor_from_surface(
        surface, color=np.array([1, 0, 0]), opacity=1.0, smooth="heavy"
    ):
        n_points = surface.GetNumberOfPoints()
        if n_points < 2:
            print("Not enough points in surface")
            return None
        # print(f"Generating actor from surface with {n_points} points")

        # https://kitware.github.io/vtk-examples/site/Python/Modelling/SmoothDiscreteMarchingCubes/
        if smooth == "light":
            feature_angle = 120.0
            pass_band = 0.001
            smoothing_iterations = 10
        elif smooth == "heavy":
            feature_angle = 120.0
            pass_band = 0.001
            smoothing_iterations = 50
        else:
            feature_angle = 120.0
            pass_band = 0.001
            smoothing_iterations = 20

        smoother = vtk.vtkWindowedSincPolyDataFilter()
        smoother.SetInputData(surface)
        smoother.SetNumberOfIterations(smoothing_iterations)
        smoother.FeatureEdgeSmoothingOff()
        smoother.BoundarySmoothingOff()
        smoother.NonManifoldSmoothingOn()
        smoother.NormalizeCoordinatesOn()
        smoother.SetFeatureAngle(feature_angle)
        smoother.SetPassBand(pass_band)
        smoother.Update()

        normals = vtk.vtkPolyDataNormals()
        normals.SetInputConnection(smoother.GetOutputPort())
        normals.ComputePointNormalsOn()
        normals.ComputeCellNormalsOn()
        normals.Update()

        # for debug purposes dump surface to file
        # writer = vtkXMLPolyDataWriter()
        # writer.SetFileName(r"C:\data\CardiacCTExplorer\ImageCAS-output\3.img\visualizations\debug_surface.vtp")
        # writer.SetInputConnection(normals.GetOutputPort())
        # writer.Write()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(normals.GetOutputPort())
        mapper.ScalarVisibilityOff()

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetOpacity(opacity)
        actor.GetProperty().SetColor(float(color[0]), float(color[1]), float(color[2]))

        return actor

    def generate_actors_from_segment_file_name(
        self, segm_name, color_name, opacity, smooth="heavy"
    ):
        if not os.path.exists(segm_name):
            # print(f"No {segm_name}")
            return
        surface = surfutils.convert_label_map_to_surface(segm_name)
        if surface is not None:
            rgba = [0.0, 0.0, 0.0, 0.0]
            vtk.vtkNamedColors().GetColor(color_name, rgba)
            actor = self.generate_actor_from_surface(
                surface, rgba, opacity, smooth=smooth
            )
            if actor is not None:
                self.actors.append(actor)

    def generate_actors_from_segment_itk_labelmap(
        self, segm_itk, segment_id, color_name, opacity, smooth="heavy"
    ):
        surface = surfutils.convert_sitk_image_to_surface(segm_itk, segment_id)
        if surface is not None:
            rgba = [0.0, 0.0, 0.0, 0.0]
            vtk.vtkNamedColors().GetColor(color_name, rgba)
            actor = self.generate_actor_from_surface(
                surface, rgba, opacity, smooth=smooth
            )
            if actor is not None:
                self.actors.append(actor)



class RenderCardiacData(RenderTotalSegmentatorData):
    """Can render data from CardiacCTExplorer."""
    def __init__(self, win_size, ct_img, label_img, verbose=False, quiet=True, render_to_file=True):
        super().__init__(win_size, render_to_file=render_to_file)
        try:
            tool_version = importlib.metadata.version("CardiacCTExplorer")
        except importlib.metadata.PackageNotFoundError:
            tool_version = "unknown"
        if tool_version is not None and tool_version != "":
            self.message_text += f"CardiacCTExplorer version: {tool_version}\n"

        if label_img is not None:
            self.generate_actors_from_segment_itk_labelmap(label_img, 1,"LightBlue", 0.2)
            self.generate_actors_from_segment_itk_labelmap(label_img, 2,"DarkSlateBlue", 1.0, smooth="medium")
            self.generate_actors_from_segment_itk_labelmap(label_img, 3,"DarkRed", 1.0, smooth="medium")
            self.generate_actors_from_segment_itk_labelmap(label_img, 8,"DarkOliveGreen", 1.0, smooth="medium")
            self.generate_actors_from_segment_itk_labelmap(label_img, 9,"LightCoral", 0.4, smooth="medium")
        self.viewport_3d_1 = [0.0, 0.0, 0.35, 0.5]
        self.viewport_3d_2 = [0.0, 0.5, 0.35, 1.0]
        self.viewport_3d_3 = [0.35, 0.0, 0.70, 0.5]
        self.viewport_text = [0.7, 0.0, 1.0, 0.40]
        self.viewport_volume = [0.35, 0.5, 0.70, 1.0]
        self.viewport_plot = [0.0, 0.0, 0.0, 0.0]
        self.viewport_slice_1 = [0.7, 0.40, 1.0, 0.60]
        self.viewport_slice_2 = [0.7, 0.60, 1.0, 0.80]
        self.viewport_slice_3 = [0.7, 0.80, 1.0, 1.0]

        self.ren_3d_1 = None
        self.ren_3d_2 = None
        self.ren_3d_3 = None
        self.ren_slice_1 = None
        self.ren_slice_2 = None
        self.ren_slice_3 = None

        self.setup_renderers()

    # https://en.wikipedia.org/wiki/Web_colors
    def setup_renderers(self):
        self.ren_3d_1 = vtk.vtkRenderer()
        self.ren_3d_1.SetViewport(self.viewport_3d_1)
        self.ren_3d_1.SetBackground(vtk.vtkNamedColors().GetColor3d("LightSteelBlue"))

        self.ren_win.AddRenderer(self.ren_3d_1)
        self.ren_3d_2 = vtk.vtkRenderer()
        self.ren_3d_2.SetViewport(self.viewport_3d_2)
        self.ren_3d_2.SetBackground(vtk.vtkNamedColors().GetColor3d("DimGray"))

        self.ren_win.AddRenderer(self.ren_3d_2)
        self.ren_3d_3 = vtk.vtkRenderer()
        self.ren_3d_3.SetViewport(self.viewport_3d_3)
        self.ren_3d_3.SetBackground(vtk.vtkNamedColors().GetColor3d("Azure"))

        self.ren_win.AddRenderer(self.ren_3d_3)

        for actor in self.actors:
            self.ren_3d_1.AddActor(actor)
            self.ren_3d_2.AddActor(actor)
            self.ren_3d_3.AddActor(actor)
            # self.ren_3d_4.AddActor(actor)

        actor_bounds = self.ren_3d_1.ComputeVisiblePropBounds()
        c = [(actor_bounds[0] + actor_bounds[1]) / 2, (actor_bounds[2] + actor_bounds[3]) / 2,
             (actor_bounds[4] + actor_bounds[5]) / 2]

        self.ren_3d_1.GetActiveCamera().SetParallelProjection(1)
        self.ren_3d_1.GetActiveCamera().SetViewUp(0, 0, 1)
        self.ren_3d_1.GetActiveCamera().SetPosition(c[0], c[1] - 400, c[2])
        self.ren_3d_1.GetActiveCamera().SetFocalPoint(c[0], c[1], c[2])
        self.ren_3d_1.ResetCameraScreenSpace()

        self.ren_3d_2.GetActiveCamera().SetParallelProjection(1)
        self.ren_3d_2.GetActiveCamera().SetFocalPoint(c[0], c[1], c[2])
        self.ren_3d_2.GetActiveCamera().SetViewUp(0, 0, 1)
        self.ren_3d_2.GetActiveCamera().SetPosition(c[0] + 400, c[1], c[2])
        self.ren_3d_2.ResetCameraScreenSpace()

        self.ren_3d_3.GetActiveCamera().SetParallelProjection(1)
        self.ren_3d_3.GetActiveCamera().SetFocalPoint(c[0], c[1], c[2])
        self.ren_3d_3.GetActiveCamera().SetViewUp(0, 0, 1)
        self.ren_3d_3.GetActiveCamera().SetPosition(c[0], c[1] + 400, c[2])
        self.ren_3d_3.ResetCameraScreenSpace()

        # Renderer for text
        self.ren_text = vtk.vtkRenderer()
        self.ren_win.AddRenderer(self.ren_text)
        self.ren_text.SetViewport(self.viewport_text)
        self.ren_slice_1 = vtk.vtkRenderer()
        self.ren_win.AddRenderer(self.ren_slice_1)
        self.ren_slice_1.SetViewport(self.viewport_slice_1)
        self.ren_slice_2 = vtk.vtkRenderer()
        self.ren_win.AddRenderer(self.ren_slice_2)
        self.ren_slice_2.SetViewport(self.viewport_slice_2)
        self.ren_slice_3 = vtk.vtkRenderer()
        self.ren_win.AddRenderer(self.ren_slice_3)
        self.ren_slice_3.SetViewport(self.viewport_slice_3)


    def set_precomputed_slice(self, base_name):
        """
        Here the slices are precomputed as png file
        """
        plane_file_1 = f'{base_name}_slice_1_rgb_crop.png'
        plane_file_2 = f'{base_name}_slice_2_rgb_crop.png'
        plane_file_3 = f'{base_name}_slice_3_rgb_crop.png'

        png_reader_1 = vtk.vtkPNGReader()
        if os.path.exists(plane_file_1) and png_reader_1.CanReadFile(plane_file_1):
            png_reader_1.SetFileName(plane_file_1)
            png_reader_1.Update()

            image_viewer = vtk.vtkImageViewer2()
            image_viewer.SetInputConnection(png_reader_1.GetOutputPort())
            image_viewer.SetRenderWindow(self.ren_win)
            image_viewer.SetRenderer(self.ren_slice_1)
            self.ren_slice_1.GetActiveCamera().ParallelProjectionOn()
            self.ren_slice_1.ResetCameraScreenSpace()

        png_reader_2 = vtk.vtkPNGReader()
        if os.path.exists(plane_file_2) and png_reader_2.CanReadFile(plane_file_2):
            png_reader_2.SetFileName(plane_file_2)
            png_reader_2.Update()

            image_viewer = vtk.vtkImageViewer2()
            image_viewer.SetInputConnection(png_reader_2.GetOutputPort())
            image_viewer.SetRenderWindow(self.ren_win)
            image_viewer.SetRenderer(self.ren_slice_2)
            self.ren_slice_2.GetActiveCamera().ParallelProjectionOn()
            self.ren_slice_2.ResetCameraScreenSpace()

        png_reader_3 = vtk.vtkPNGReader()
        if os.path.exists(plane_file_3) and png_reader_3.CanReadFile(plane_file_3):
            png_reader_3.SetFileName(plane_file_3)
            png_reader_3.Update()

            image_viewer = vtk.vtkImageViewer2()
            image_viewer.SetInputConnection(png_reader_3.GetOutputPort())
            image_viewer.SetRenderWindow(self.ren_win)
            image_viewer.SetRenderer(self.ren_slice_3)
            self.ren_slice_3.GetActiveCamera().ParallelProjectionOn()
            self.ren_slice_3.ResetCameraScreenSpace()
