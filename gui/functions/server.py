# Python 3 server example
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import numpy as np
from PIL import Image
from astropy.io import fits
from sharpcap_capture import get_latest_sharpcap_image


hostName = "192.168.0.45"
serverPort = 8080
latest_image = None


def save_as_latest_image_png(p):
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


class MyServer(BaseHTTPRequestHandler):
    def display_latest_image(self):
        path = get_latest_sharpcap_image()
        if latest_image != path:
            save_as_latest_image_png(path)
        self._show_gui()

    def show_latest(self):
        path = get_latest_sharpcap_image()
        if latest_image != path:
            save_as_latest_image_png(path)
        f = open("latest.png", 'rb')
        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(f.read())
        f.close()

    def _show_gui(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
        self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        self.wfile.write(bytes("<form action=\"display\" method=\"post\"> "
                               "<input type=\"submit\" value=\"Display latest image\" /> "
                               "</form>", "utf-8"))
        self.wfile.write(bytes("<p>This is an example web server.</p> "
                               "<form action=\"home\" method=\"get\"> "
                               "<input type=\"submit\" value=\"HOME\" /> "
                               "</form>", "utf-8"))

        self.wfile.write(bytes("<p>Do something else</p> "
                               "<form action=\"omg\" method=\"post\"> "
                               "<input type=\"text\" value=\"0\" name=\"test_name\"/> "
                               "<input type=\"text\" value=\"1\" name=\"other_name\"/> "
                               "<input type=\"submit\" value=\"Go to Google\" /> "
                               "</form>", "utf-8"))
        im_path = os.path.join(os.getcwd(), "latest.png")
        picture_line = "<picture>"\
                       "<source srcset=\"latest.png\" type=\"image/png\">"\
                       "<img src=\"latest.png\" alt=\"Latest\">"\
                       "</picture>"

        image_line = "<img src=\"latest.png\" alt=\"Latest image\">"
        print(f"Image line = {picture_line}")
        self.wfile.write(bytes(picture_line, "utf-8"))

        self.wfile.write(bytes("</body></html>", "utf-8"))

    def do_POST(self):
        method = self.path.split('/')[-1]
        content_len = int(self.headers.get('Content-Length', 0))
        post_body = self.rfile.read(content_len).decode('utf-8')
        if len(post_body) > 1:
            form_kv = post_body.split('&')
            form_dict = {s.split('=')[0]:s.split('=')[1] for s in form_kv}
            print(f"Method = {method}, Post body = {post_body}, dict={form_dict}")

        if method in post_actions:
            post_actions[method](self)
        else:
            self._show_gui()

    def do_GET(self):
        self._show_gui()


post_actions["display"] = MyServer.show_latest


if __name__ == "__main__":
    path = get_latest_sharpcap_image()
    save_as_latest_image_png(path)

    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
