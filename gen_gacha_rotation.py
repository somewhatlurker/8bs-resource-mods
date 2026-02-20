# Generate yearly gacha rotation, based on series in spreadsheet (csv).
# Consists of:
#  - A permanent "premium gacha" lineup that is always available (PERMANENT_CSV_PATH)
#  - A list of limited series, which occur at a given ISO week number, and are expected
#    to end within the same ISO week as they begin
#  - Limited cards will be available in gacha alongside the permanent lineup
#  - The cycle repeats yearly

# THIS IS A WORK IN PROGRESS! CURRENTLY ONLY LOADS/PARSES DATA!

from gacha_data.load_gacha_data import load_and_parse_gacha_data_csv


LIMITED_CSV_PATH = 'gacha_data/limited_rotation.csv'
PERMANENT_CSV_PATH = 'gacha_data/permanent.csv'


limited_gacha_data = load_and_parse_gacha_data_csv(LIMITED_CSV_PATH)
print(limited_gacha_data)

permanent_gacha_data = load_and_parse_gacha_data_csv(PERMANENT_CSV_PATH)
print(permanent_gacha_data)
