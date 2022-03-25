from http.server import BaseHTTPRequestHandler, HTTPServer
import numpy as np
from PIL import Image
from astropy.io import fits
import os
from functions.coordinate_mover import CoordinateMover
from functions.sharpcap_capture import get_latest_sharpcap_image, get_second_latest_sharpcap_image

hostName = "192.168.0.45"
serverPort = 8080


class LatestImageCache:
    def __init__(self):
        self._cache = None

    def update(self, p):
        if self._cache != p:
            self._cache = p
            return True
        return False


latest_image = LatestImageCache()


def save_as_latest_image_png(p):
    print(f"Opening {p}")
    with fits.open(p) as hdul:
        raw_data = hdul[0].data
        max_int = 65535
        h, w = raw_data.shape
        grid_nw = 16
        grid_nh = 10
        indices_w = np.linspace(0, w, grid_nw).astype(np.int16)[1:-1]
        indices_h  = np.linspace(0, h, grid_nh).astype(np.int16)[1:-1]
        print(f"Indices  ={indices_w}")
        raw_data[:, indices_w] = max_int
        raw_data[indices_h, :] = max_int

        im_data = np.log(raw_data)
        b = np.min(im_data)
        e = np.max(im_data)
        a = max_int/(e - b)
        normalized = np.multiply(np.subtract(im_data, b), a).astype(np.uint16)
        print(f"min = {np.min(normalized)}, max = {np.max(normalized)}")
        Image.fromarray(normalized).save('latest.png')


post_actions = {}
post_actions_no_args = {}
html_replacements = {}
index_html_text = ""


class DefaultRequestHandler(BaseHTTPRequestHandler):
    def _replace_in_index(self):
        new_html = self.server._index_html_text
        for k, v in html_replacements.items():
            replacement = v(self)
            new_html = new_html.replace(k, str(replacement))

        return new_html

    def _show_path(self, p):
        if latest_image.update(p):
            save_as_latest_image_png(p)
        with open("latest.png", 'rb') as f:
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.end_headers()
            self.wfile.write(f.read())

    def dec_correction(self, fdict):
        if not "correction_value" in fdict:
            return
        value_str = fdict["correction_value"]
        # try:
        value = float(value_str)
        # except
        print(f"Value = {value}")
        self.server.set_dec_correction(value)
        self._show_gui()

    def go_back_ra(self):
        self.server.go_back_ra()
        self._show_gui()

    def show_latest(self, fdict):
        print("showing latest")
        self._show_path(get_latest_sharpcap_image())

    def show_previous(self, fdict):
        print("showing previous")
        self._show_path(get_second_latest_sharpcap_image())

    def get_dec_correction(self):
        return self.server.get_dec_correction()

    def get_path(self):
        return self.path

    def _show_gui(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html = self._replace_in_index()
        self.wfile.write(bytes(html, "utf-8"))

    def do_POST(self):
        method = self.path.split('/')[-1]
        content_len = int(self.headers.get('Content-Length', 0))
        post_body = self.rfile.read(content_len).decode('utf-8')
        if len(post_body) > 1:
            form_kv = post_body.split('&')
            form_dict = {s.split('=')[0]:s.split('=')[1] for s in form_kv}
            print(f"Method = {method}, Post body = {post_body}, dict={form_dict}")

        if method in post_actions:
            post_actions[method](self, form_dict)
        elif method in post_actions_no_args:
            post_actions_no_args[method](self)
        else:
            self._show_gui()

    def do_GET(self):
        self._show_gui()


html_replacements = {
    "@SELF_REQUEST": DefaultRequestHandler.get_path,
    "@DEC_CORRECTION": DefaultRequestHandler.get_dec_correction
}

post_actions["display_latest"] = DefaultRequestHandler.show_latest
post_actions["display_previous"] = DefaultRequestHandler.show_previous
post_actions["dec_correction"] = DefaultRequestHandler.dec_correction
post_actions_no_args["go_back_ra"] = DefaultRequestHandler.go_back_ra


class PEliminatorServer(HTTPServer):
    def __init__(self, mover: CoordinateMover, **kwargs):
        HTTPServer.__init__(self, **kwargs)
        self._mover = mover
        index_abs_path = os.path.join(os.path.dirname(__file__), "index.html")
        with open(index_abs_path) as f:
            self._index_html_text = f.read()

    def set_dec_correction(self, value):
        self._mover.set_dec_drift(value)

    def get_dec_correction(self):
        return self._mover.get_dec_correction()

    def go_back_ra(self):
        self._mover.go_back_ra()



def get_web_server(mover=None):
    web_server = PEliminatorServer(mover,
                                  server_address=(hostName, serverPort),
                                  RequestHandlerClass=DefaultRequestHandler)
    print("Server started http://%s:%s" % (hostName, serverPort))
    return web_server


if __name__ == "__main__":

    web_server = get_web_server()

    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass

    web_server.server_close()
    print("Server stopped.")
