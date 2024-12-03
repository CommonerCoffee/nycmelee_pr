import math
from scipy.stats import gmean
from collections import Counter

# Some utility functions
def spr(placing):
    if placing == 1:
        return 0
    else:
        return math.floor(math.log2(placing - 1)) + math.ceil(math.log2((2/3 * placing)))
    
def attend_list(player, dataset):
    subset = dataset[(dataset.p1_tag == player) | (dataset.p2_tag == player)]
    tourney_list = list(subset.tournament.unique())
    print(f'Total Attendance: {len(tourney_list)}\n')
    for tourney in tourney_list:
        print(tourney)

def geometric_mean(x):
    # Geometric mean is only defined for positive numbers
    x = x[x > 0]
    return gmean(x) if len(x) > 0 else np.nan

# PR Rates
# PR functions
def sum_records(df, win_loss):
    for column in df.columns:
        if '-' in column:
            a, b = column.split(' - ')
            if win_loss == 'win':
                df["pr_win"] = df[column].apply(lambda x: int(x.split(' - ')[0]))
            if win_loss == 'loss':
                df["pr_loss"] = df[column].apply(lambda x: int(x.split(' - ')[1]))
    return df

def sum_loss(df):
    df['pr_loss'] = df.apply(lambda row: sum(int(val) for val in str(row.iloc[-1]) if val.isdigit()), axis=1)
    return df

def calculate_pr_results(df, results,subsets):
    if results == "w":
        result = 0
    elif results == "l":
        result = 1
    
    if subsets is None:     
        curr = 0
        for col in df.columns:
            curr += df[col].apply(lambda x: int(x.split(' - ')[result]))
    else:       
        curr = 0
        for col in df.columns[subsets[0]:subsets[1]]:
            curr += df[col].apply(lambda x: int(x.split(' - ')[result]))

    return curr

def get_ranges(number):
    rnge = number // 3
    range1 = [0, rnge]
    range2 = [range1[1], range1[1] + rnge]
    range3 = [range2[1], number]
    return [range1, range2, range3]

# Player Comparison Helpers
def compare_two(dataset, player1, player2):
    players = [player1, player2]
    subset = dataset[dataset['player'].isin(players)].set_index('player')
    subset = subset.drop(columns=['all_attendance','nc_attendance','non_nc_attendance','avg_nc_placing'])
    subset = subset.loc[:, subset.min() > 0]
    print(player1, np.count_nonzero(np.array(subset.loc[player1]) < np.array(subset.loc[player2])))
    print(player2, np.count_nonzero(np.array(subset.loc[player2]) < np.array(subset.loc[player1])))
    return subset

def enumerate_and_count(lst):
    if isinstance(lst, float) and math.isnan(lst):
        return 'NaN'
    # Enumerate the list and count occurrences
    counted_elements = Counter(lst)

    # Convert the Counter object to a list of tuples
    result_list = list(counted_elements.items())
    sorted_result = sorted(result_list, key=lambda x: x[0])
    formatted_output = ', '.join(f'{element} ({count})' if count > 1 else f'{element}' for element, count in sorted_result)

    return formatted_output
