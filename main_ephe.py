import urllib.request
import shutil

if __name__ == '__main__':
    # for i in range(1000):
    #     num = str(i)
    #     num = (3 - len(num)) * '0' + num
    #     url = f'https://www.astro.com/ftp/swisseph/ephe/ast431/s431{num}s.se1'
    #     print(url)
    #     file_name = f'/tmp/ephe/s431{num}s.se1'
    #     with urllib.request.urlopen(url) as response, open(file_name, 'wb') as out_file:
    #         shutil.copyfileobj(response, out_file)

    fname = 'sefstars.txt'
    file_name = f'/tmp/ephe/' + fname
    url = f'https://www.astro.com/ftp/swisseph/ephe/' + fname
    with urllib.request.urlopen(url) as response, open(file_name, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)

