import io
import qrcode

if __name__ == '__main__':
    qr = qrcode.QRCode(border=0, box_size=25, version=1)
    # qr.add_data("http://астрогор.онлайн")
    qr.add_data("http://astrogor.com")
    m = qr.get_matrix()
    s = ''
    for i in range(len(m)):
        for j in range(len(m[0])):
            if m[i][j]:
                s += '0'
            else:
                s += '.'
        s += '\n'
    print(s)


    # f = io.StringIO()
    # qr.print_ascii(out=f)
    # f.seek(0)
    # print(f.read())

    print(qr)