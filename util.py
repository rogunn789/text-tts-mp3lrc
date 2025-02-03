import os, shutil


def formattime(t):
    if t / 10 == 0:
        return '0' + str(t)
    else:
        return str(t)


def ms2time(t):
    m = int(t / 60000)
    t = int(t % 60000)
    s = int(t / 1000)
    t = int(t % 1000)
    minsec = formattime(m) + ':' + formattime(s) + '.' + str(t)
    return minsec


def get_valid_filename(name):
    s = str(name).strip()
    filename = ''
    for chr in s:
        if chr not in '/\\[]':
            filename += chr
    return filename


def delete_dir(folder):
    try:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))
    except FileNotFoundError:
        print('')