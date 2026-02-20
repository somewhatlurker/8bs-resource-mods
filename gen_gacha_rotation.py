# Generate yearly gacha rotation, based on series in spreadsheet (csv).
# Consists of:
#  - A permanent "premium gacha" lineup that is always available (PERMANENT_CSV_PATH)
#  - A list of limited series, which occur at a given ISO week number, and are expected
#    to end within the same ISO week as they begin
#  - Limited cards will be available in gacha alongside the permanent lineup
#  - The cycle repeats yearly

# THIS IS A WORK IN PROGRESS! CURRENTLY ONLY LOADS/PARSES DATA!

from gacha_data.load_gacha_data import load_and_parse_gacha_data_csv, verify_gacha_data
from util import read_json_decrypted


LIMITED_CSV_PATH = 'gacha_data/limited_rotation.csv'
PERMANENT_CSV_PATH = 'gacha_data/permanent.csv'


def gen_gacha_rotation(resource_path, ver):
    limited_gacha_data = load_and_parse_gacha_data_csv(LIMITED_CSV_PATH)
    verify_gacha_data(limited_gacha_data)
    print(limited_gacha_data)

    permanent_gacha_data = load_and_parse_gacha_data_csv(PERMANENT_CSV_PATH)
    verify_gacha_data(permanent_gacha_data)
    print(permanent_gacha_data)

    master_chara = read_json_decrypted(resource_path, ver, 'master_chara.json')
    master_series = read_json_decrypted(resource_path, ver, 'master_series.json')

if __name__ == '__main__':
    from sys import argv

    if len(argv) != 3:
        print('Usage: python gen_gacha_rotation.py <resource_path> <ver>')
        print('Example: python gen_gacha_rotation.py res 733')
        exit()

    gen_gacha_rotation(argv[1], int(argv[2]))
