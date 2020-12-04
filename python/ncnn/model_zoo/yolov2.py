import ncnn
from .model_store import get_model_file
from ..utils.objects import Detect_Object

class MobileNet_YoloV2:
    def __init__(self, target_size=416, num_threads=1, use_gpu=False):
        self.target_size  = target_size
        self.num_threads = num_threads
        self.use_gpu = use_gpu

        self.mean_vals = [1.0, 1.0, 1.0]
        self.norm_vals = [0.007843, 0.007843, 0.007843]

        self.net = ncnn.Net()
        self.net.opt.use_vulkan_compute = self.use_gpu

        # original pretrained model from https://github.com/eric612/MobileNet-YOLO
        # https://github.com/eric612/MobileNet-YOLO/blob/master/models/yolov2/mobilenet_yolo_deploy.prototxt
        # https://github.com/eric612/MobileNet-YOLO/blob/master/models/yolov2/mobilenet_yolo_deploy_iter_80000.caffemodel
        # the ncnn model https://github.com/caishanli/pyncnn-assets/tree/master/models
        self.net.load_param(get_model_file("mobilenet_yolo.param"))
        self.net.load_model(get_model_file("mobilenet_yolo.bin"))

        self.class_names = ["background",
            "aeroplane", "bicycle", "bird", "boat",
            "bottle", "bus", "car", "cat", "chair",
            "cow", "diningtable", "dog", "horse",
            "motorbike", "person", "pottedplant",
            "sheep", "sofa", "train", "tvmonitor"]

    def __del__(self):
        self.net = None

    def __call__(self, img):
        img_h = img.shape[0]
        img_w = img.shape[1]

        mat_in = ncnn.Mat.from_pixels_resize(img, ncnn.Mat.PixelType.PIXEL_BGR, img.shape[1], img.shape[0], self.target_size, self.target_size)
        mat_in.substract_mean_normalize([], self.norm_vals)
        mat_in.substract_mean_normalize(self.mean_vals, [])

        ex = self.net.create_extractor()
        ex.set_num_threads(self.num_threads)

        ex.input("data", mat_in)

        mat_out = ncnn.Mat()
        ex.extract("detection_out", mat_out)

        objects = []

        #printf("%d %d %d\n", mat_out.w, mat_out.h, mat_out.c)
        
        #method 1, use ncnn.Mat.row to get the result, no memory copy
        for i in range(mat_out.h):
            values = mat_out.row(i)

            obj = Detect_Object()
            obj.label = values[0]
            obj.prob = values[1]
            obj.rect.x = values[2] * img_w
            obj.rect.y = values[3] * img_h
            obj.rect.w = values[4] * img_w - obj.rect.x
            obj.rect.h = values[5] * img_h - obj.rect.y

            objects.append(obj)
            
        '''
        #method 2, use ncnn.Mat->numpy.array to get the result, no memory copy too
        out = np.array(mat_out)
        for i in range(len(out)):
            values = out[i]
            obj = Detect_Object()
            obj.label = values[0]
            obj.prob = values[1]
            obj.rect.x = values[2] * img_w
            obj.rect.y = values[3] * img_h
            obj.rect.w = values[4] * img_w - obj.rect.x
            obj.rect.h = values[5] * img_h - obj.rect.y
            objects.append(obj)
        '''

        return objects