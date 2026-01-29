import sys
import time
import requests
import pandas as pd
import numpy as np
import json
import ast
import datetime
from dateutil.relativedelta import relativedelta, FR
from bs4 import BeautifulSoup
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter("ignore", UserWarning)



class Database:

    def __init__(self, authToken):
        self.authToken = authToken

    def get_hk_stock_ohlc(self, code, start_date, end_date, freq, price_adj=False, vol_adj=False, anchor=False):

        if not price_adj and not vol_adj: anchor = False

        check_bool_dict = self.check_hk_stock_ohlc_args(code, start_date, end_date, freq)

        if False not in list(check_bool_dict.values()):
            link_url = 'http://www.hkfdb.net/data_api?'
            token_str = 'token=' + str(self.authToken)
            database_str = 'database=' + 'hk_stock_ohlc'
            code_str = 'code=' + code
            start_date_str = 'start_date=' + str(start_date)
            end_date_str = 'end_date=' + str(end_date)
            freq_str = 'freq=' + freq
            price_adj_str = 'price_adj=0' if price_adj == False else 'price_adj=1'
            vol_adj_str = 'vol_adj=0' if vol_adj == False else 'vol_adj=1'
            link_str = link_url + code_str + '&' + token_str + '&' + database_str + '&' + start_date_str + '&' + \
                       end_date_str + '&' + freq_str + '&' + price_adj_str + '&' + vol_adj_str

            response = requests.get(link_str)
            response_ok = response_check(response)
            if response_ok == True:

                if price_adj == False:
                    json1 = json.loads(response.content).replace("'", "\"").replace('False', '0').replace('True','1').replace(
                        'nan', 'NaN')
                    ohlc_result = json.loads(json1)
                else:
                    json1 = json.loads(response.content).replace("'", "\"").replace('[(', '\"[(').replace(')]',
                                                                                                          ')]\"').replace(
                        'False', '0').replace('True', '1').replace('nan', 'NaN')

                    result = json.loads(json1)
                    ohlc_result = result[0]

                    qfq_result = result[1].replace('[', '').replace(']', '').replace(' ', '')
                    qfq_result = ast.literal_eval(qfq_result)
                    adj_df = pd.DataFrame(qfq_result, columns=['date', 'adj_factor'])

                df_list = []

                for item in ohlc_result:
                    date_int = item['_id']
                    df = pd.DataFrame(item['content'])

                    if len(df) > 0:
                        df['date'] = str(date_int)
                        df_list.append(df)

                df = pd.concat(df_list)

                if 'T' in freq:
                    df['time'] = df['time'].astype(str)
                    df['datetime'] = df['date'] + ' ' + df['time']
                    df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d %H%M%S')
                    cols = ['datetime', 'date', 'time', 'open', 'high', 'low', 'close', 'volume']

                elif freq == '1D':
                    df['datetime'] = df['date']
                    df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d')
                    cols = ['datetime', 'date', 'open', 'high', 'low', 'close', 'volume']

                elif freq == '1DW':
                    df['datetime'] = df['date']
                    df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d')
                    cols = ['datetime', 'date', 'open', 'high', 'low', 'close', 'volume', 'susp', 'auc_close',
                            'adj_close', 'gross_volume', 'turnover', 'VWAP']
                    df['susp'] = df['susp'].astype(bool)

                df = df[cols]
                df = df.set_index(keys='datetime')
                df = df.sort_index()

                if price_adj == True:

                    adj_df = adj_df[adj_df['date'] > 20100000]

                    def propagate_adj_factor(row, last_value):
                        if row["adj_factor"] != 1:
                            last_value[0] = row["adj_factor"]
                        return last_value[0]

                    last_value = [1]
                    adj_df["adj_factor"] = adj_df.apply(lambda row: propagate_adj_factor(row, last_value), axis=1)

                    if anchor:
                        adj_df = adj_df[adj_df['date'] >= start_date]
                        adj_df = adj_df[adj_df['date'] <= end_date]

                        anchor_factor = adj_df.at[adj_df.index[0], 'adj_factor'] / 1
                        adj_df['adj_factor'] = adj_df['adj_factor'] / anchor_factor
                        adj_df = adj_df.reset_index(drop=True)

                    adj_df['adj_factor'] = adj_df['adj_factor'].round(3)

                    adj_df = adj_df.iloc[::-1].reset_index(drop=True)
                    adj_df['date'] = adj_df['date'].astype(str)
                    first_date = adj_df.loc[adj_df.index[0], 'date']
                    min_date_of_ohlc_df = df['date'].min()
                    if int(first_date) > int(min_date_of_ohlc_df):
                        first_date = min_date_of_ohlc_df

                    last_date = str(max([int(adj_df.loc[adj_df.index[-1], 'date']), int(df.loc[df.index[-1], 'date'])]))

                    if '-' in adj_df.at[0, 'date']:
                        adj_df['date'] = pd.to_datetime(adj_df['date'], format='%Y-%m-%d')
                    else:
                        adj_df['date'] = pd.to_datetime(adj_df['date'], format='%Y%m%d')

                    adj_df = adj_df.set_index(keys='date')
                    t_index = pd.DatetimeIndex(pd.date_range(start=first_date, end=last_date, freq='1D'))

                    adj_df = adj_df.reindex(t_index)
                    adj_df = adj_df.fillna(method='bfill')
                    adj_df = adj_df.fillna(method='ffill')
                    adj_df = adj_df.reset_index()

                    adj_df['index'] = adj_df['index'].astype(str)
                    adj_df['index'] = adj_df['index'].str.replace('-', '', regex=False)
                    df = pd.merge(left=df, left_on='date', right=adj_df, right_on='index')

                    if df['adj_factor'].isnull().values.any():
                        df['adj_factor'] = df['adj_factor'].fillna(method='ffill')

                    if 'T' in freq:
                        df['datetime'] = df['date'] + ' ' + df['time']
                        df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d %H%M%S')
                    else:
                        df['datetime'] = df['date']
                        df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d')

                    df = df.set_index(keys='datetime')

                    if vol_adj == True:
                        if freq == '1DW':
                            col_list = ['open', 'high', 'low', 'close', 'volume', 'gross_volume']
                        else:
                            col_list = ['open', 'high', 'low', 'close', 'volume']
                    else:
                        col_list = ['open', 'high', 'low', 'close']

                    for col in col_list:
                        df[col] = df[col] * df['adj_factor']
                        if 'volume' not in col:
                            df[col] = df[col].map(lambda x: round(x, 3))
                        else:
                            df[col] = df[col].map(lambda x: round(x, 0))
                            df[col] = df[col].astype(int)

                    if 'T' in freq:
                        df = df[['date', 'time', 'open', 'high', 'low', 'close', 'volume']]
                    else:
                        if freq == '1DW':
                            df = df[['date', 'open', 'high', 'low', 'close', 'volume', 'susp',
                                     'auc_close', 'gross_volume', 'turnover', 'VWAP']]
                        elif freq == '1D':
                            df = df[['date', 'open', 'high', 'low', 'close', 'volume']]

                df['date'] = df['date'].astype(int)
                if 'T' in freq:
                    df['time'] = df['time'].astype(int)
                else:
                    df['time'] = 0

                df = df[['date', 'time', 'open', 'high', 'low', 'close', 'volume']]

                return df

    def get_us_stock_ohlc(self, code, start_date, end_date):

        check_bool_dict = self.check_us_stock_ohlc_args(code, start_date, end_date)

        if False not in list(check_bool_dict.values()):
            link_url = 'http://www.hkfdb.net/data_api?'
            token_str = 'token=' + str(self.authToken)
            database_str = 'database=' + 'spx_stock_ohlc'
            code_str = 'code=' + code
            start_date_str = 'start_date=' + str(start_date)
            end_date_str = 'end_date=' + str(end_date)
            link_str = link_url + code_str + '&' + token_str + '&' + database_str + '&' + start_date_str + '&' + \
                       end_date_str

            response = requests.get(link_str)
            response_ok = response_check(response)
            if response_ok == True:

                result = json.loads(json.loads(response.content).replace("'", "\""))

                df_list = []
                for item in result:
                    date_int = item['_id']
                    df = pd.DataFrame(item['content'])
                    if len(df) > 0:
                        cols = ['datetime', 'date'] + list(df.columns)
                        df['time'] = df['time'].astype(str)
                        df['date'] = str(date_int)
                        df['datetime'] = df['date'] + ' ' + df['time'].str.zfill(6)
                        df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d %H%M%S')

                        df = df[cols]
                        df = df.set_index(keys='datetime')

                        df_list.append(df)

                df = pd.concat(df_list)
                df = df.sort_index()

                return df

        else:
            err_msg = 'Error in: '
            for error in check_bool_dict:
                if check_bool_dict[error] == False:
                    err_msg += error + ','
            print(err_msg)

    ## Futures
    expiry_dict = {}
    rolling_day = 0
    rolling_time = 0

    def apply_rolling_day(self, row):
        rolling_day = self.rolling_day
        rolling_time = self.rolling_time

        if row.current_month_expiry_date_diff < rolling_day:  # less than rolling_day, keep next month
            if not row.current_month:  # next month, keep it
                return True
            else:
                return False

        elif row.current_month_expiry_date_diff > rolling_day:  # more than rolling_dat, keep current
            if row.current_month:  # current month, keep it
                return True
            else:
                return False

        else:  # current_month_expiry_date_diff == rolling_day, need to consider time
            if row.time >= rolling_time:  # need to keep next month
                if not row.current_month:  # next month, keep it
                    return True
                else:
                    return False

            else:  # need to keep current month
                if row.current_month:  # next month, keep it
                    return True
                else:
                    return False

    def apply_rolling_1D(self, row):
        rolling_day = self.rolling_day

        if row.current_month_expiry_date_diff <= rolling_day:  # less than rolling_day, keep next month
            if not row.current_month:  # next month, keep it
                return True
            else:
                return False

        elif row.current_month_expiry_date_diff > rolling_day:  # more than rolling_dat, keep current
            if row.current_month:  # current month, keep it
                return True
            else:
                return False

    def apply_RTH_ATH(self, row):
        if (row.time > 90000 and row.time < 163000):
            return True
        else:
            return False

    def apply_roll_diff(self, row):
        rolling_day = self.rolling_day
        rolling_time = self.rolling_time
        roll_diff = self.roll_diff
        if row.current_month_expiry_date_diff == rolling_day and row.time == rolling_time:
            return roll_diff
        else:
            return 0

    def get_hk_fut_ohlc(self, index, start_date, end_date, freq, rolling_day, rolling_time=0, rth_only=False):

        check_bool_dict = self.check_hk_fut_ohlc_args(index, freq, start_date, end_date, rolling_day, rolling_time)

        self.rolling_day = rolling_day
        self.rolling_time = rolling_time

        if False not in list(check_bool_dict.values()):

            link_url = 'http://www.hkfdb.net/data_api?'
            token = str(self.authToken)
            start_date_str = str(start_date)
            end_date_str = str(end_date)
            link_str = f'{link_url}token={token}&database=hk_futures_ohlc&index={index}&freq={freq}&start_date={start_date_str}&end_date={end_date_str}'

            response = requests.get(link_str)
            response_ok = response_check(response)

            if response_ok == True:

                result_list = json.loads(
                    json.loads(response.content).replace("'", "\"").replace("True", "true").replace("False", "false"))

                columns = ['datetime', 'open', 'high', 'low', 'close', 'volume',
                           'trade_date_mask', 'expiry_date', 'current_month',
                           'current_month_expiry_date', 'current_month_expiry_date_diff']

                if freq == '1D':
                    dfs = []
                    for item in list(reversed(result_list)):
                        df_single = pd.DataFrame(item['content'], columns=columns)
                        df_single['datetime'] = pd.to_datetime(df_single['datetime'])
                        df_single['date'] = pd.to_datetime(df_single['datetime']).dt.strftime('%Y%m%d').astype(int)
                        df_single['time'] = pd.to_datetime(df_single['datetime']).dt.strftime('%H%M%S').astype(int)
                        df_single['RTH'] = df_single.apply(self.apply_RTH_ATH, axis=1)

                        if rth_only:
                            df_single = df_single[df_single['RTH'] == True]
                        else:
                            df_single = df_single[df_single['RTH'] == False]  # only 1D

                        df_all = []

                        for current_month in [True, False]:
                            df_current = df_single[df_single['current_month'] == current_month].sort_values(
                                by=['datetime']).reset_index(drop=True)
                            df = df_current.head(1).copy()

                            if len(df) > 0:
                                df['open'] = df_current.at[0, 'open']
                                df['high'] = df_current['high'].max()
                                df['low'] = df_current['low'].min()
                                df['close'] = df_current.at[len(df) - 1, 'close']
                                df['volume'] = df_current['volume'].sum()

                                df_all.append(df.copy())

                        if len(df_all) > 0:
                            dfs.append(pd.concat(df_all))

                    if len(dfs) == 0:
                        column_names = ['datetime', 'date', 'time', 'open', 'high', 'low', 'close', 'volume',
                                        'expiry_date', 'roll_diff']
                        df = pd.DataFrame(columns=column_names)
                        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
                        df['date'] = df['date'].astype(str)

                        return df

                    df = pd.concat(dfs)
                    df['datetime'] = pd.to_datetime(df['datetime'])

                    ## Find the valid expiry date to processed , ie within date range
                    expiry_dates = list(df['expiry_date'].unique())
                    expiry_dates.sort()

                    # # Calculate roll diff
                    roll_diff_dict = {}

                    for expiry_date in expiry_dates:
                        try:
                            exact_rolling_date = df[(df['expiry_date'] == expiry_date) &
                                                    (df['current_month_expiry_date_diff'] == rolling_day) &
                                                    (df['current_month'] == True)].reset_index(drop=True).sort_values(
                                by=['datetime'], ascending=False).at[0, 'date']

                            df_roll = df[(df['date'] == exact_rolling_date)].copy()
                            df_roll = df_roll.sort_values(by=['datetime']).reset_index(drop=True)

                            roll_diff_dict[expiry_date] = {}

                            roll_diff = df_roll.at[0, 'close'] - df_roll.at[1, 'close']
                            roll_diff_dict[expiry_date]['rolling_day'] = exact_rolling_date
                            roll_diff_dict[expiry_date]['roll_diff'] = roll_diff
                        except:
                            pass

                    df = df.sort_values(by=['datetime']).reset_index(drop=True)

                    df['roll_diff'] = 0

                    for expiry_date in roll_diff_dict.keys():
                        d = roll_diff_dict[expiry_date]['rolling_day']
                        diff = roll_diff_dict[expiry_date]['roll_diff']

                        condition = (df['date'] == d) & (df['current_month'] == False)
                        indices = df[condition].index[0]
                        df.at[indices, 'roll_diff'] = diff

                    df['keep'] = df.apply(self.apply_rolling_1D, axis=1)
                    df = df[df['keep'] == True]
                    selected_columns = ['datetime', 'date', 'time', 'open', 'high', 'low', 'close', 'volume',
                                        'expiry_date', 'roll_diff']
                    df = df[selected_columns]
                    df = df.sort_values(by=['datetime']).set_index('datetime', drop=True)

                    df.index = df.index.strftime('%Y-%m-%d')
                    df.index = pd.to_datetime(df.index)
                    df['time'] = 0
                    df['open'] = df['open'].astype(int)
                    df['high'] = df['high'].astype(int)
                    df['low'] = df['low'].astype(int)
                    df['close'] = df['close'].astype(int)

                    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
                    df['date'] = df['date'].astype(str)

                    return df


                else:  # 1T, 5T, 15T
                    df_list = []
                    for item in result_list:
                        date_int = item['_id']
                        df = pd.DataFrame(item['content'], columns=columns)
                        if len(df) > 0:
                            df['date'] = str(date_int)
                            df_list.append(df)
                    if len(df_list) == 0:
                        column_names = ['datetime', 'date', 'time', 'open', 'high', 'low', 'close', 'volume',
                                        'expiry_date', 'roll_diff']
                        df = pd.DataFrame(columns=column_names)
                        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
                        df['date'] = df['date'].astype(str)

                        return df

                    df = pd.concat(df_list, )

                    df['datetime'] = pd.to_datetime(df['datetime'])

                    df = df.copy()
                    df['date'] = pd.to_datetime(df['datetime']).dt.strftime('%Y%m%d').astype(int)
                    df['time'] = pd.to_datetime(df['datetime']).dt.strftime('%H%M%S').astype(int)
                    condition = df['time'] == 120000  # remove 120000 time
                    df = df[~condition]
                    df['RTH'] = df.apply(self.apply_RTH_ATH, axis=1)  # Determine RTH and ATH

                    ## Find the valid expiry date to processed , ie within date range
                    expiry_dates = list(df['expiry_date'].unique())
                    expiry_dates.sort()
                    # print(expiry_dates)

                    # Calculate roll diff
                    roll_diff_dict = {}

                    for expiry_date in expiry_dates:

                        try:
                            exact_rolling_date = df[(df['expiry_date'] == expiry_date) &
                                                    (df['current_month_expiry_date_diff'] == rolling_day) &
                                                    (df['current_month'] == True)].sort_values(by=['datetime'],
                                                                                               ascending=False).reset_index(
                                drop=True).reset_index(drop=True).at[0, 'date']
                            # Sorting Reverse because get later date to make sure it is RTH trading date

                            df_roll = df[(df['date'] == exact_rolling_date)].copy()
                            df_roll = df_roll[df_roll['time'] == rolling_time].sort_values(
                                by=['expiry_date']).reset_index(drop=True)

                            roll_diff_dict[expiry_date] = {}

                            if len(df_roll) == 2:  # Got date on exact rolling date and both current and next month present
                                roll_diff = df_roll.at[0, 'close'] - df_roll.at[1, 'close']
                                roll_diff_dict[expiry_date]['rolling_day'] = exact_rolling_date
                                roll_diff_dict[expiry_date]['roll_diff'] = roll_diff
                                roll_diff_dict[expiry_date]['rolling_time'] = rolling_time

                            else:  # length of df_roll is zero
                                df_roll = df[(df['date'] == exact_rolling_date) & (df['RTH'] == True)].copy()
                                # last_row = 0
                                # if not (len(df_roll) == 1): ## something only 1 row, investigate laster
                                #     # Cannot find rolling time, assume roll at RTH last trade
                                #     df_roll = df[(df['date'] == exact_rolling_date) & (df['RTH'] == True)].copy()
                                #     last_row = 1

                                df_roll = df_roll.sort_values(by=['time', 'expiry_date']).reset_index(drop=True)
                                df_roll = df_roll.tail(2).sort_values(by=['expiry_date']).reset_index(drop=True)
                                # print(df_roll)
                                roll_diff = df_roll.at[0, 'close'] - df_roll.at[1, 'close']
                                roll_diff_dict[expiry_date]['rolling_day'] = exact_rolling_date
                                roll_diff_dict[expiry_date]['roll_diff'] = roll_diff
                                roll_diff_dict[expiry_date]['rolling_time'] = df_roll.at[0, 'time']

                        except Exception as e:
                            try:
                                roll_diff_dict.pop(expiry_date)
                            except:
                                pass
                            pass

                    df = df.reset_index(drop=True)
                    df['roll_diff'] = 0

                    for expiry_date in roll_diff_dict.keys():
                        d = roll_diff_dict[expiry_date]['rolling_day']
                        t = roll_diff_dict[expiry_date]['rolling_time']
                        diff = roll_diff_dict[expiry_date]['roll_diff']

                        condition = (df['date'] == d) & (df['time'] == t) & (df['current_month'] == False)
                        indices = df[condition].index[0]
                        df.at[indices, 'roll_diff'] = diff

                    ## Exclude ATH if needed
                    if rth_only:
                        df = df[df['RTH'] == True]

                    ## Calculate rolling day and determine keep or not
                    df['keep'] = df.apply(self.apply_rolling_day, axis=1)
                    df = df[df['keep'] == True]
                    selected_columns = ['datetime', 'date', 'time', 'open', 'high', 'low', 'close', 'volume',
                                        'expiry_date', 'RTH', 'roll_diff']
                    df = df[selected_columns]
                    df = df.sort_values(by=['datetime']).set_index('datetime', drop=True)

                    df['time'] = df['time'].astype(str).str.zfill(6)
                    df['open'] = df['open'].astype(int)
                    df['high'] = df['high'].astype(int)
                    df['low'] = df['low'].astype(int)
                    df['close'] = df['close'].astype(int)
                    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
                    df['date'] = df['date'].astype(str)

                    return df


        else:
            err_msg = 'Error in: '
            for error in check_bool_dict:
                if check_bool_dict[error] == False:
                    err_msg += error + ','
            print(err_msg)

    # # Old fut
    # def get_hk_fut_ohlc(self, index, start_date, end_date, freq, rolling_day, rolling_time=0, rth_only=False):
    #
    #     check_bool_dict = self.check_hk_fut_ohlc_args(index, freq, start_date, end_date, rolling_day, rolling_time)
    #
    #     if False not in list(check_bool_dict.values()):
    #
    #         if freq == '1D':
    #             rolling_time = 0
    #             if rth_only == True:
    #                 freq = freq + '_rth'
    #             elif rth_only == False:
    #                 freq = freq + '_all'
    #
    #         start_date_dt = datetime.datetime.strptime(str(start_date), '%Y%m%d').date()
    #         end_date_dt = datetime.datetime.strptime(str(end_date), '%Y%m%d').date()
    #
    #         if start_date_dt.month > 1:
    #             start_date_year = start_date_dt.year
    #         else:
    #             start_date_year = start_date_dt.year - 1
    #             start_date_dt = start_date_dt - relativedelta(months=1)
    #
    #         end_date_year = end_date_dt.year if end_date_dt.month < 11 else end_date_dt.year + 1
    #
    #         holiday_dict = get_hk_holiday_and_expiry_date(start_date_year, end_date_year, 'datetime')
    #         expiry_date_list = holiday_dict['expiry_date']
    #
    #         expiry_date_dict = {}
    #         for expiry_date in expiry_date_list:
    #             expiry_year_month_str = str(expiry_date.year - 2000) + str(expiry_date.month).zfill(2)
    #             expiry_date_dict[expiry_year_month_str] = expiry_date
    #
    #         day_diff = (end_date_dt - start_date_dt).days
    #
    #         year_month_involved_list = []
    #         for i in range(day_diff + 1):
    #             i_date = start_date_dt + datetime.timedelta(days=i)
    #             year_month = i_date.strftime('%y%m')
    #             expiry_date = expiry_date_dict[year_month]
    #             if i_date > expiry_date:
    #                 year_month = (i_date + relativedelta(months=1)).strftime('%y%m')
    #             if year_month not in year_month_involved_list:
    #                 year_month_involved_list.append(year_month)
    #
    #         year_month_involved_list.append(
    #             (datetime.datetime.strptime(year_month_involved_list[-1], '%y%m') + relativedelta(months=1)).strftime(
    #                 '%y%m'))
    #         year_month_involved_list_str = json.dumps(str(year_month_involved_list))
    #
    #         year_month_involved_list_str = year_month_involved_list_str.replace('[', '')
    #         year_month_involved_list_str = year_month_involved_list_str.replace(']', '')
    #         year_month_involved_list_str = year_month_involved_list_str.replace('\'', '')
    #         year_month_involved_list_str = year_month_involved_list_str.replace(',', '')
    #         year_month_involved_list_str = year_month_involved_list_str.replace(' ', '_')
    #         year_month_involved_list_str = year_month_involved_list_str.replace('\"', '')
    #
    #         link_url = 'http://www.hkfdb.net/data_api?'
    #         token_str = 'token=' + str(self.authToken)
    #         database_str = 'database=' + 'hk_fut_ohlc'
    #         index_str = 'index=' + index
    #         freq_str = 'freq=' + freq
    #         start_date_str = 'start_date=' + str(start_date)
    #         end_date_str = 'end_date=' + str(end_date)
    #         rolling_day_str = 'rolling_day=' + str(rolling_day)
    #         rolling_time_str = 'rolling_time=' + str(rolling_time)
    #         year_month_involved_list_str = 'year_month_involved_list=' + year_month_involved_list_str
    #         link_str = link_url + index_str + '&' + freq_str + '&' + rolling_day_str + '&' + rolling_time_str + \
    #                    '&' + year_month_involved_list_str + '&' \
    #                    + token_str + '&' + database_str + '&' \
    #                    + start_date_str + '&' + end_date_str
    #
    #         response = requests.get(link_str)
    #         response_ok = response_check(response)
    #         if response_ok == True:
    #
    #             result_list = json.loads(json.loads(response.content).replace("'", "\""))
    #
    #             df_list = []
    #             date_time_list_list = []
    #             date_time_intersect_list = []
    #             for result in result_list:
    #                 sub_df_list = []
    #                 for item in result:
    #                     df = pd.DataFrame(item['content'])
    #                     if len(df) > 0:
    #                         sub_df_list.append(df)
    #
    #                 if len(sub_df_list) > 0:
    #                     df = pd.concat(sub_df_list)
    #                     df = df.reset_index(drop=True)
    #                     temp_date_list = list(df['date'].unique())
    #                     temp_date_list.sort()
    #
    #                     date_list = []
    #                     for temp_date in temp_date_list:
    #                         if datetime.datetime.strptime(str(temp_date), '%Y%m%d').weekday() < 5:
    #                             date_list.append(temp_date)
    #
    #                     front_year_month = str(date_list[0])[2:6]
    #                     back_year_month = str(date_list[-1])[2:6]
    #                     front_expiry_date = int(expiry_date_dict[front_year_month].strftime('%Y%m%d'))
    #                     back_expiry_date = int(expiry_date_dict[back_year_month].strftime('%Y%m%d'))
    #                     for i in range(len(date_list)):
    #                         date_item = date_list[i]
    #
    #                         if i + rolling_day <= len(date_list) - 1:
    #                             if date_list[i + rolling_day] == front_expiry_date:
    #                                 front_cut_off_date = date_item
    #                             elif date_list[i + rolling_day] == back_expiry_date:
    #                                 back_cut_off_date = date_item
    #                                 break
    #                         else:
    #                             back_cut_off_date = max(date_list)
    #
    #                     if df.loc[0, 'expiry_date'] == '20130530':
    #                         front_cut_off_date = 20130501
    #
    #                     if (back_cut_off_date != end_date) or (
    #                             back_cut_off_date == end_date and back_cut_off_date not in expiry_date_list):
    #                         if '1D' not in freq:
    #                             df_front = df[(df['date'] == front_cut_off_date) & (df['time'] == rolling_time)]
    #                             df_back  = df[(df['date'] == back_cut_off_date) & (df['time'] == rolling_time)]
    #
    #                             df = df[(df['date'] > front_cut_off_date) | (
    #                                         (df['date'] == front_cut_off_date) & (df['time'] > rolling_time))]
    #                             df = df[(df['date'] < back_cut_off_date) | (
    #                                         (df['date'] == back_cut_off_date) & (df['time'] < rolling_time))]
    #
    #                             df = pd.concat([df, df_front, df_back])
    #
    #                         else:
    #                             df = df[(df['date'] > front_cut_off_date) | (df['date'] == front_cut_off_date)]
    #                             df = df[(df['date'] < back_cut_off_date) | (df['date'] == back_cut_off_date)]
    #
    #                     df = df[df['date'] >= start_date]
    #                     df = df[df['date'] <= end_date]
    #                     df['date'] = df['date'].astype(str)
    #                     if '1D' not in freq:
    #                         df['time'] = df['time'].astype(str)
    #                         df['time'] = df['time'].str.zfill(6)
    #                         df['datetime'] = df['date'] + ' ' + df['time']
    #                     else:
    #                         df['datetime'] = df['date']
    #
    #                     df = df.reset_index(drop=True)
    #                     date_time_list = df['datetime'].to_list()
    #
    #                     df = df.sort_values(by='datetime')
    #
    #                     if '1D' not in freq:
    #                         # if len(date_time_list_list) > 0:
    #                         #     date_time_intersect = (set(date_time_list_list).intersection(date_time_list))
    #                         #     if len(date_time_intersect) == 0:
    #                         #         df_list.append(df)
    #                         # else:
    #                         #     df_list.append(df)
    #                         df_list.append(df)
    #
    #                     else:
    #                         date_time_intersect = (set(date_time_list_list).intersection(date_time_list))
    #                         date_time_intersect = list(date_time_intersect)
    #                         if len(date_time_intersect) > 0:
    #                             date_time_intersect_list.append(date_time_intersect[0])
    #                         df_list.append(df)
    #
    #                     date_time_list_list += date_time_list
    #
    #             df = pd.concat(df_list)
    #
    #             if '1D' not in freq:
    #                 cols = ['datetime', 'date', 'time', 'open', 'high', 'low', 'close', 'volume', 'expiry_date', 'RTH']
    #
    #             else:
    #                 cols = ['datetime', 'date', 'time', 'open', 'high', 'low', 'close', 'volume', 'expiry_date']
    #                 df['time'] = 0
    #
    #             if '1D' not in freq:
    #                 df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d %H%M%S')
    #                 df['RTH'] = df['RTH'].astype(bool)
    #             else:
    #                 df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d')
    #
    #             df = df[cols]
    #             df['roll_diff'] = 0
    #
    #             if '1D' in freq:
    #                 drop_index_list = []
    #                 df = df.reset_index()
    #                 for date_time_intersect in date_time_intersect_list:
    #                     check_drop_index_row = df[df['date'] == date_time_intersect]
    #                     if len(check_drop_index_row) > 1:
    #                         index_0 = check_drop_index_row.index[0]
    #                         index_1 = check_drop_index_row.index[1]
    #                         expiry_date_0 = df.loc[index_0, 'expiry_date']
    #                         expiry_date_1 = df.loc[index_1, 'expiry_date']
    #                         close_price_0 = df.loc[index_0, 'close']
    #                         close_price_1 = df.loc[index_1, 'close']
    #                         if expiry_date_0 > expiry_date_1:
    #                             drop_index_list.append(index_1)
    #                             roll_diff = close_price_0 - close_price_1
    #                             df.at[index_0,'roll_diff'] = roll_diff
    #                         elif expiry_date_0 < expiry_date_1:
    #                             drop_index_list.append(index_0)
    #                             roll_diff = close_price_1 - close_price_0
    #                             roll_diff = close_price_0 - close_price_1
    #                             df.at[index_1,'roll_diff'] = roll_diff
    #                 if len(drop_index_list) > 0:
    #                     df = df.drop(drop_index_list, axis=0)
    #                 df = df.drop('index', axis=1)
    #
    #             else:
    #                 df = df.reset_index()
    #
    #                 duplicates = df[df.duplicated(subset=['datetime'], keep=False)]
    #                 min_expiry_row_index_list = []
    #
    #                 for dt in duplicates['datetime'].unique():
    #                     df2 = duplicates[duplicates['datetime'] == dt]
    #                     min_expiry = df2['expiry_date'].min()
    #                     max_expiry = df2['expiry_date'].max()
    #                     min_expiry_row = df2.loc[df2['expiry_date'] == min_expiry]
    #                     max_expiry_row = df2.loc[df2['expiry_date'] == max_expiry]
    #                     min_expiry_row_index = min_expiry_row.index[0]
    #                     max_expiry_row_index  = max_expiry_row.index[0]
    #                     min_expiry_close = min_expiry_row['close'].values[0]
    #                     max_expiry_close = max_expiry_row['close'].values[0]
    #
    #                     roll_diff = min_expiry_close - max_expiry_close
    #
    #                     min_expiry_row_index_list.append(min_expiry_row_index)
    #                     df.at[max_expiry_row_index, 'roll_diff'] = roll_diff
    #
    #                 if len(min_expiry_row_index_list) > 0:
    #                     df = df.drop(min_expiry_row_index_list, axis=0)
    #                 df = df.drop('index', axis=1)
    #
    #             df = df.set_index(keys='datetime')
    #             df = df.sort_index(ascending=True)
    #
    #             if '1D' not in freq and rth_only == True:
    #                 df = df[df['RTH'] == True]
    #
    #             #df = df.drop_duplicates(keep='first')
    #
    #             return df
    #
    #     else:
    #         err_msg = 'Error in: '
    #         for error in check_bool_dict:
    #             if check_bool_dict[error] == False:
    #                 err_msg += error + ','
    #         print(err_msg)

    def get_hk_market_cap_hist_by_date(self, start_date, end_date):

        check_bool_dict = self.check_start_end_date(start_date, end_date)

        if False not in list(check_bool_dict.values()):
            link_url = 'http://www.hkfdb.net/data_api?'
            token_str = 'token=' + str(self.authToken)
            database_str = 'database=' + 'hk_market_cap_hist_by_date'
            start_date_str = 'start_date=' + str(start_date)
            end_date_str = 'end_date=' + str(end_date)
            link_str = link_url + '&' + token_str + '&' + database_str + '&' + start_date_str + '&' + end_date_str

            response = requests.get(link_str)
            response_ok = response_check(response)
            if response_ok == True:

                json_content = json.loads(response.content)
                json_content = json_content.replace(' nan', '\" nan\"')

                result = json.loads(json_content.replace("'", "\""))

                df_list = []
                for item in result:
                    date_int = item['_id']
                    df = pd.DataFrame(item['content'])
                    if len(df) > 0:
                        df['date'] = str(date_int)
                        df_list.append(df)
                df = pd.concat(df_list)

                df = df.sort_values(['date', 'market_cap_mil'], ascending=[True, False])
                df = df.reset_index(drop=True)

                if '-' in df.at[0, 'date']:
                    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
                else:
                    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')

                df = df[['date', 'code', 'issued_share_mil', 'market_cap_mil', 'cumulative_market_cap_mil']]
                df = df[df['date'].dt.weekday < 5]
                return df

        else:
            err_msg = 'Error in: '
            for error in check_bool_dict:
                if check_bool_dict[error] == False:
                    err_msg += error + ','
            print(err_msg)

    def get_hk_market_cap_hist_by_code(self, code):
        check_bool_dict = self.check_hk_code_args(code)

        if False not in list(check_bool_dict.values()):
            link_url = 'http://www.hkfdb.net/data_api?'
            token_str = 'token=' + str(self.authToken)
            database_str = 'database=' + 'hk_market_cap_hist_by_code'
            code_str = 'code=' + str(code)
            link_str = link_url + '&' + token_str + '&' + database_str + '&' + code_str

            response = requests.get(link_str)
            response_ok = response_check(response)
            if response_ok == True:

                json_content = json.loads(response.content)
                json_content = json_content.replace(' nan', '\" nan\"')
                result = json.loads(json_content.replace("'", "\""))

                df_list = []
                for item in result:
                    date_int = item['_id']
                    df = pd.DataFrame(item['content'])
                    if len(df) > 0:
                        df['date'] = str(date_int)
                        df_list.append(df)
                df = pd.concat(df_list)

                df = df.sort_values(by='date')
                df = df.reset_index(drop=True)
                if '-' in df.at[0, 'date']:
                    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
                else:
                    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
                df = df[['date', 'code', 'issued_share_mil', 'market_cap_mil', 'cumulative_market_cap_mil']]
                df = df.set_index('date')
                df = df[~df.index.duplicated(keep='first')]

                df2 = df[df.index >= '2023-02-20']
                df = df[df.index < '2023-02-20']

                index_end_date = datetime.datetime.now() + datetime.timedelta(days=1)
                index_end_year = index_end_date.year
                date_index = pd.date_range(start='2023-02-20', end=index_end_date.strftime('%Y-%m-%d'), freq='1D')
                df2 = df2.reindex(date_index)
                df2 = df2.shift(-1)
                df = pd.concat([df, df2])
                df = df.dropna()

                # holiday_list = get_hk_holiday_and_expiry_date(2023, index_end_year, format='dt')['public_holiday']
                # df = df[~df.index.isin(holiday_list)]
                df = df[df.index.weekday < 5]

                return df

        else:
            err_msg = 'Error in: '
            for error in check_bool_dict:
                if check_bool_dict[error] == False:
                    err_msg += error + ','
            print(err_msg)

    def get_hk_buyback_by_code(self, code, agg_value=False):

        link_url = 'http://www.hkfdb.net/data_api?'
        token_str = 'token=' + str(self.authToken)
        database_str = 'database=' + 'hk_buyback_by_code'
        code_str = 'code=' + code
        link_str = link_url + code_str + '&' + token_str + '&' + database_str

        response = requests.get(link_str)
        response_ok = response_check(response)
        if response_ok == True:

            result = json.loads(json.loads(response.content).replace("'", "\""))

            df = pd.DataFrame(result)
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            df = df.set_index(keys='date')
            df = df.sort_index()

            if agg_value == True:
                df = df[['value']]
                df = df.groupby(df.index).agg({'value': sum})

            return df

    def get_hk_buyback_by_date(self, start_date, end_date):

        check_bool_dict = self.check_start_end_date(start_date, end_date)

        if False not in list(check_bool_dict.values()):

            link_url = 'http://www.hkfdb.net/data_api?'
            token_str = 'token=' + str(self.authToken)
            database_str = 'database=' + 'hk_buyback_by_date'
            start_date_str = 'start_date=' + str(start_date)
            end_date_str = 'end_date=' + str(end_date)
            link_str = link_url + '&' + token_str + '&' + database_str + '&' + start_date_str + '&' + end_date_str

            response = requests.get(link_str)
            response_ok = response_check(response)
            if response_ok == True:

                json_content = json.loads(response.content)
                json_content = json_content.replace(' nan', '\" nan\"')

                result = ast.literal_eval(json_content)

                df_list = []
                for item in result:
                    date_int = item['_id']
                    df = pd.DataFrame(item['content'])
                    if len(df) > 0:
                        df['date'] = str(date_int)
                        df_list.append(df)
                df = pd.concat(df_list)

                df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
                df = df.set_index(keys='date')
                df = df.sort_index()

                return df
        else:
            err_msg = 'Error in: '
            for error in check_bool_dict:
                if check_bool_dict[error] == False:
                    err_msg += error + ','
            print(err_msg)

    def get_hk_shortsell_by_code(self, code):

        link_url = 'http://www.hkfdb.net/data_api?'
        token_str = 'token=' + str(self.authToken)
        database_str = 'database=' + 'hk_shortsell_by_code'
        code_str = 'code=' + code
        link_str = link_url + code_str + '&' + token_str + '&' + database_str

        response = requests.get(link_str)
        response_ok = response_check(response)
        if response_ok == True:
            result = json.loads(json.loads(response.content).replace("'", "\""))

            df = pd.DataFrame(result)
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            df = df.set_index(keys='date')
            df = df.sort_index()

            df['ss_ratio'] = df['ss_ratio'].astype(float)
            df['ss_shares'] = df['ss_shares'].astype(float)
            df['ss_dollars'] = df['ss_dollars'].astype(float)

            return df

    def get_hk_shortsell_by_date(self, start_date, end_date):

        check_bool_dict = self.check_start_end_date(start_date, end_date)

        if False not in list(check_bool_dict.values()):

            link_url = 'http://www.hkfdb.net/data_api?'
            token_str = 'token=' + str(self.authToken)
            database_str = 'database=' + 'hk_shortsell_by_date'
            start_date_str = 'start_date=' + str(start_date)
            end_date_str = 'end_date=' + str(end_date)
            link_str = link_url + '&' + token_str + '&' + database_str + '&' + start_date_str + '&' + end_date_str

            response = requests.get(link_str)
            response_ok = response_check(response)
            if response_ok == True:

                json_content = json.loads(response.content)
                json_content = json_content.replace(' nan', '\" nan\"')

                result = ast.literal_eval(json_content)

                df_list = []
                for item in result:
                    date_int = item['_id']
                    df = pd.DataFrame(item['content'])
                    if len(df) > 0:
                        df['date'] = str(date_int)
                        df_list.append(df)
                df = pd.concat(df_list)

                df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
                df = df.set_index(keys='date')
                df = df.sort_index()

                return df
        else:
            err_msg = 'Error in: '
            for error in check_bool_dict:
                if check_bool_dict[error] == False:
                    err_msg += error + ','
            print(err_msg)

    def get_hk_earning_calendar_by_code(self, code):

        link_url = 'http://www.hkfdb.net/data_api?'
        token_str = 'token=' + str(self.authToken)
        database_str = 'database=' + 'hk_earning_calendar_by_code'
        code_str = 'code=' + code
        link_str = link_url + code_str + '&' + token_str + '&' + database_str

        response = requests.get(link_str)
        response_ok = response_check(response)
        if response_ok == True:
            result = json.loads(json.loads(response.content).replace("'", "\""))

            df = pd.DataFrame(result)
            df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d %H:%M:%S')
            df = df.set_index(keys='datetime')
            df = df.sort_index()

            return df

    def get_hk_earning_calendar_by_date(self, start_date, end_date):

        check_bool_dict = self.check_start_end_date(start_date, end_date)

        if False not in list(check_bool_dict.values()):
            link_url = 'http://www.hkfdb.net/data_api?'
            token_str = 'token=' + str(self.authToken)
            database_str = 'database=' + 'hk_earning_calendar_by_date'
            start_date_str = 'start_date=' + str(start_date)
            end_date_str = 'end_date=' + str(end_date)
            link_str = link_url + '&' + token_str + '&' + database_str + '&' + start_date_str + '&' + end_date_str

            response = requests.get(link_str)
            response_ok = response_check(response)
            if response_ok == True:

                result = ast.literal_eval(json.loads(response.content))

                df_list = []
                for item in result:
                    date_int = item['_id']
                    df = pd.DataFrame(item['content'])
                    if len(df) > 0:
                        df['date'] = str(date_int)
                        df_list.append(df)
                df = pd.concat(df_list)

                df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d%H%M%S')

                df = df.set_index(keys='datetime')
                df = df[['code', 'name', 'result']]
                df = df.sort_index()
                return df

        else:
            err_msg = 'Error in: '
            for error in check_bool_dict:
                if check_bool_dict[error] == False:
                    err_msg += error + ','
            print(err_msg)

    def get_us_earning_calendar_by_code(self, code):

        link_url = 'http://www.hkfdb.net/data_api?'
        token_str = 'token=' + str(self.authToken)
        database_str = 'database=' + 'us_earning_calendar_by_code'
        code_str = 'code=' + code
        link_str = link_url + code_str + '&' + token_str + '&' + database_str

        response = requests.get(link_str)
        response_ok = response_check(response)
        if response_ok == True:

            result = ast.literal_eval(json.loads(response.content))

            temp_list = list(result)
            date_list = []
            for date in temp_list:
                date_list.append(datetime.datetime.strptime(date, '%Y-%m-%d').date())

            return date_list

    def get_us_earning_calendar_by_date(self, start_date, end_date):

        check_bool_dict = self.check_start_end_date(start_date, end_date)

        if False not in list(check_bool_dict.values()):
            link_url = 'http://www.hkfdb.net/data_api?'
            token_str = 'token=' + str(self.authToken)
            database_str = 'database=' + 'us_earning_calendar_by_date'
            start_date_str = 'start_date=' + str(start_date)
            end_date_str = 'end_date=' + str(end_date)
            link_str = link_url + '&' + token_str + '&' + database_str + '&' + start_date_str + '&' + end_date_str

            response = requests.get(link_str)
            response_ok = response_check(response)
            if response_ok == True:

                result = json.loads(json.loads(response.content).replace("'", "\""))

                df_list = []
                for item in result:
                    date_int = item['_id']
                    df = pd.DataFrame(item['content'])
                    if len(df) > 0:
                        df['date'] = str(date_int)
                        df_list.append(df)
                df = pd.concat(df_list)
                df = df[['date', 'code']]

                df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')

                df = df.set_index(keys='date')
                df = df.sort_index()
                return df

        else:
            err_msg = 'Error in: '
            for error in check_bool_dict:
                if check_bool_dict[error] == False:
                    err_msg += error + ','
            print(err_msg)

    def get_ccass_by_code(self, code, start_date, end_date):

        check_bool_dict = self.check_ccass_by_code_args(code, start_date, end_date)

        if False not in list(check_bool_dict.values()):
            link_url = 'http://www.hkfdb.net/data_api?'
            token_str = 'token=' + str(self.authToken)
            database_str = 'database=' + 'ccass_by_code'
            code_str = 'code=' + code
            start_date_str = 'start_date=' + str(start_date)
            end_date_str = 'end_date=' + str(end_date)
            link_str = link_url + code_str + '&' + token_str + '&' + database_str + '&' + start_date_str + '&' + end_date_str

            response = requests.get(link_str)
            response_ok = response_check(response)
            if response_ok == True:

                result = json.loads(json.loads(response.content).replace("'", "\""))

                df_list = []
                for item in result:
                    date_int = item['_id']
                    df = pd.DataFrame(item['content'])
                    df['date'] = str(date_int)
                    df_list.append(df)

                df = pd.concat(df_list)
                df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
                df = df.set_index('date')
                df = df.sort_index()

                for col in df.columns:
                    if 'participants_participant_' in col:
                        df = df.rename(columns={col: col.replace('participants_participant_', 'participants_')})

                df['total_non_ccass_participants_shares'] = df['total_issued_shares'] - df[
                    'total_ccass_participants_shares']

                df = df[~df.index.weekday.isin([5, 6])]

                return df

        else:
            err_msg = 'Error in: '
            for error in check_bool_dict:
                if check_bool_dict[error] == False:
                    err_msg += error + ','
            print(err_msg)

    def get_ccass_holding_rank(self, code, start_date, end_date):

        check_bool_dict = self.check_ccass_holding_rank_args(code, start_date, end_date)

        if False not in list(check_bool_dict.values()):
            link_url = 'http://www.hkfdb.net/data_api?'
            token_str = 'token=' + str(self.authToken)
            database_str = 'database=' + 'ccass_holding_rank'
            code_str = 'code=' + code
            start_date_str = 'start_date=' + str(start_date)
            end_date_str = 'end_date=' + str(end_date)
            link_str = link_url + code_str + '&' + token_str + '&' + database_str + '&' + start_date_str + '&' + end_date_str

            response = requests.get(link_str)
            response_ok = response_check(response)
            if response_ok == True:
                res = json.loads(response.content)
                res = res.replace("'", "\"")
                res = res.replace(" \"S", "\"\"S")
                res = res.replace("\"S", "S")

                result = json.loads(res)

                df_list = []
                for item in result:
                    date_int = item['_id']
                    df = pd.DataFrame(item['content'])
                    if len(df) > 0:
                        df['date'] = date_int
                        df_list.append(df)

                df = pd.concat(df_list)

                df = df.sort_values(['date', 'share'], ascending=False)
                df = df[['date', 'ccass_id', 'name', 'share', 'percent']]
                df = df.reset_index(drop=True)
                df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')

                df = df[~df['date'].dt.weekday.isin([5, 6])]

                return df

        else:
            err_msg = 'Error in: '
            for error in check_bool_dict:
                if check_bool_dict[error] == False:
                    err_msg += error + ','
            print(err_msg)

    def get_ccass_all_id(self):

        link_url = 'http://www.hkfdb.net/data_api?'
        token_str = 'token=' + str(self.authToken)
        database_str = 'database=' + 'ccass_all_id'
        link_str = link_url + '&' + token_str + '&' + database_str

        response = requests.get(link_str)
        response_ok = response_check(response)
        if response_ok == True:
            result = ast.literal_eval(json.loads(response.content))

            df = pd.DataFrame(result)

            return df

    def get_ccass_by_id(self, ccass_id, start_date, end_date):

        check_bool_dict = self.check_ccass_by_id_args(ccass_id, start_date, end_date)

        if False not in list(check_bool_dict.values()):
            link_url = 'http://www.hkfdb.net/data_api?'
            token_str = 'token=' + str(self.authToken)
            database_str = 'database=' + 'ccass_by_id'
            ccass_id_str = 'ccass_id=' + ccass_id
            start_date_str = 'start_date=' + str(start_date)
            end_date_str = 'end_date=' + str(end_date)
            link_str = link_url + ccass_id_str + '&' + token_str + '&' + database_str + '&' + start_date_str + '&' + \
                       end_date_str

            response = requests.get(link_str)
            response_ok = response_check(response)
            if response_ok == True:

                res = json.loads(response.content)
                res = res.replace(': nan', ': \"nan"')
                result = json.loads(res.replace("'", "\""))

                df_list = []
                for item in result:
                    date_int = item['_id']
                    df = pd.DataFrame(item['content'])
                    if len(df) > 0:
                        df['date'] = str(date_int)
                        df_list.append(df)

                df = pd.concat(df_list)

                df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')

                df = df[['date', 'code', 'percent', 'share']]
                df = df.set_index(keys='date')
                df = df.sort_index()
                df = df[~df.index.weekday.isin([5, 6])]

                INT_32_RANGE = 2 ** 32
                df['share'] = df['share'].apply(lambda x: x + INT_32_RANGE if x < 0 else x)

                return df

        else:
            err_msg = 'Error in: '
            for error in check_bool_dict:
                if check_bool_dict[error] == False:
                    err_msg += error + ','
            print(err_msg)

    def get_ccass_by_id_change(self, ccass_id, start_date, end_date):

        check_bool_dict = self.check_ccass_by_id_args(ccass_id, start_date, end_date)

        if False not in list(check_bool_dict.values()):
            start_date_dt = datetime.datetime.strptime(str(start_date), '%Y%m%d')
            end_date_dt = datetime.datetime.strptime(str(end_date), '%Y%m%d')
            if start_date_dt.weekday() > 4:
                start_date_dt = start_date_dt + relativedelta(weekday=FR(-1))
                start_date = int(start_date_dt.strftime('%Y%m%d'))
            if end_date_dt.weekday() > 4:
                end_date_dt = end_date_dt + relativedelta(weekday=FR(-1))
                end_date = int(end_date_dt.strftime('%Y%m%d'))

            link_url = 'http://www.hkfdb.net/data_api?'
            token_str = 'token=' + str(self.authToken)
            database_str = 'database=' + 'ccass_by_id'
            ccass_id_str = 'ccass_id=' + ccass_id
            start_date_str = 'start_date=' + str(start_date)
            end_date_str = 'end_date=' + str(start_date)
            link_str = link_url + ccass_id_str + '&' + token_str + '&' + database_str + '&' + start_date_str + '&' + \
                       end_date_str

            response = requests.get(link_str)

            response_ok = response_check(response)
            if response_ok == True:

                result = json.loads(json.loads(response.content).replace("'", "\""))
                df_list = []
                for item in result:
                    date_int = item['_id']
                    df = pd.DataFrame(item['content'])
                    if len(df) > 0:
                        df['date'] = str(date_int)
                        df_list.append(df)

                df_first = pd.concat(df_list)

                time.sleep(1)

                start_date_str = 'start_date=' + str(end_date)
                end_date_str = 'end_date=' + str(end_date)
                link_str = link_url + ccass_id_str + '&' + token_str + '&' + database_str + '&' + start_date_str + '&' + \
                           end_date_str

                response = requests.get(link_str)
                response_ok = response_check(response)
                if response_ok == True:

                    result = json.loads(json.loads(response.content).replace("'", "\""))

                    df_list = []
                    for item in result:
                        date_int = item['_id']
                        df = pd.DataFrame(item['content'])
                        if len(df) > 0:
                            df['date'] = str(date_int)
                            df_list.append(df)

                    df_last = pd.concat(df_list)

                    df_first = df_first.set_index(keys='code')
                    df_last = df_last.set_index(keys='code')

                    for col in df_first:
                        df_first = df_first.rename(columns={col: col + '_first'})
                        df_last = df_last.rename(columns={col: col + '_last'})

                    df_first['date_first'] = pd.to_datetime(df_first['date_first'], format='%Y%m%d')
                    df_last['date_last'] = pd.to_datetime(df_last['date_last'], format='%Y%m%d')
                    df_first = df_first[~df_first['date_first'].dt.weekday.isin([5, 6])]
                    df_last = df_last[~df_last['date_last'].dt.weekday.isin([5, 6])]

                    df = pd.concat([df_first, df_last], axis=1)
                    df['percent_chg'] = df['percent_last'] - df['percent_first']
                    df['share_chg'] = df['share_last'] - df['share_first']
                    df['date_diff'] = df['date_last'] - df['date_first']
                    df = df.dropna()

                    for col in df.columns:
                        if 'share' in col:
                            df[col] = df[col].astype(np.int64)
                    return df

        else:
            err_msg = 'Error in: '
            for error in check_bool_dict:
                if check_bool_dict[error] == False:
                    err_msg += error + ','
            print(err_msg)

    def get_spx_index_const(self, hist=True):

        link_url = 'http://www.hkfdb.net/data_api?'
        token_str = 'token=' + str(self.authToken)

        if hist == False:
            database_str = 'database=' + 'spx_index_const'
            link_str = link_url + '&' + token_str + '&' + database_str

            response = requests.get(link_str)
            response_ok = response_check(response)
            if response_ok == True:
                result = ast.literal_eval(json.loads(response.content))

                df = pd.DataFrame(result)

        else:
            database_str = 'database=' + 'spx_const_hist'
            link_str = link_url + '&' + token_str + '&' + database_str

            response = requests.get(link_str)
            result = ast.literal_eval(json.loads(response.content))

            df = pd.DataFrame(result)
            mode = df['end_date'].mode()[0]
            df['is_active'] = df['is_active'].astype(bool)
            df['is_delisted'] = df['is_delisted'].astype(bool)

            for i in range(len(df)):
                end_date = df.loc[i, 'end_date']
                if end_date == mode:
                    df.at[i, 'end_date'] = datetime.datetime.now().strftime('%Y-%m-%d')
            for col in df.columns:
                if col == 'start_date' or col == 'end_date':
                    if isinstance(df.at[0, 'start_date'], str):
                        if '-' in df.at[0, col]:
                            df[col] = pd.to_datetime(df[col], format='%Y-%m-%d')
                        else:
                            df[col] = pd.to_datetime(df[col], format='%Y%m%d')

        return df

    def get_hk_index_const(self, index_name, sort_mkt_cap=False):

        if len(index_name) > 0:

            link_url = 'http://www.hkfdb.net/data_api?'
            token_str = 'token=' + str(self.authToken)
            database_str = 'database=' + 'hk_index_const'
            index_name_str = 'index_name=' + index_name
            link_str = link_url + index_name_str + '&' + token_str + '&' + database_str

            response = requests.get(link_str)
            response_ok = response_check(response)

            if response_ok == True:

                result = ast.literal_eval(json.loads(response.content))

                df = pd.DataFrame(result)
                df['code'] = df['code'].str.zfill(5)

                for col in df.columns:
                    if col == 'start_date' or col == 'end_date':
                        if isinstance(df.at[0, 'start_date'], str):
                            if '-' in df.at[0, col]:
                                df[col] = pd.to_datetime(df[col], format='%Y-%m-%d')
                            else:
                                df[col] = pd.to_datetime(df[col], format='%Y%m%d')

                if index_name == 'hsi_const_hist':

                    df['is_alive'] = df['is_alive'].astype(bool)
                    df = df.rename(columns={'is_alive': 'is_active'})

                    for i in range(len(df)):
                        end_date = df.loc[i, 'end_date']
                        is_active = df.loc[i, 'is_active']
                        if is_active == True:
                            df.at[i, 'end_date'] = datetime.datetime.now().strftime('%Y-%m-%d')

                    for col in df.columns:
                        if col == 'start_date' or col == 'end_date':
                            if isinstance(df.at[0, 'start_date'], str):
                                if '-' in df.at[0, col]:
                                    df[col] = pd.to_datetime(df[col], format='%Y-%m-%d')
                                else:
                                    df[col] = pd.to_datetime(df[col], format='%Y%m%d')

                    df = df[['code', 'name', 'start_date', 'end_date', 'is_active']]

                if sort_mkt_cap:
                    info = self.get_basic_hk_stock_info()
                    info = info[['code', 'market_capital']]
                    df = pd.merge(df, info, on='code', how='inner')
                    df = df.sort_values(by='market_capital', ascending=False)

                return df

        else:
            err_msg = 'index_name missing'
            print(err_msg)

    def get_hk_stock_plate_const(self, plate_name, sort_mkt_cap=False):
        if len(plate_name) > 0:

            link_url = 'http://www.hkfdb.net/data_api?'
            token_str = 'token=' + str(self.authToken)
            database_str = 'database=' + 'hk_stock_plate_const'
            plate_name_str = 'plate_name=' + plate_name
            link_str = link_url + plate_name_str + '&' + token_str + '&' + database_str

            response = requests.get(link_str)
            response_ok = response_check(response)
            if response_ok == True:

                result = json.loads(json.loads(response.content).replace("'", "\""))

                df = pd.DataFrame(result)
                df['code'] = df['code'].astype(str)
                df['code'] = df['code'].str.zfill(5)

                if sort_mkt_cap:
                    info = self.get_basic_hk_stock_info()
                    info = info[['code', 'market_capital']]
                    df = pd.merge(df, info, on='code', how='inner')
                    df = df.sort_values(by='market_capital', ascending=False)

                return df

        else:
            err_msg = 'index_name missing'
            print(err_msg)

    def get_all_hk_index_name(self):

        link_url = 'http://www.hkfdb.net/data_api?'
        token_str = 'token=' + str(self.authToken)
        database_str = 'database=' + 'all_hk_index_name'
        link_str = link_url + '&' + token_str + '&' + database_str

        response = requests.get(link_str)
        response_ok = response_check(response)
        if response_ok == True:

            result = ast.literal_eval(json.loads(response.content))

            name_list = list(result)
            if 'hk_full_market' in name_list:
                name_list.remove('hk_full_market')

            return name_list

    def get_all_hk_stock_plate_name(self):

        link_url = 'http://www.hkfdb.net/data_api?'
        token_str = 'token=' + str(self.authToken)
        database_str = 'database=' + 'all_hk_stock_plate_name'
        link_str = link_url + '&' + token_str + '&' + database_str

        response = requests.get(link_str)
        response_ok = response_check(response)

        if response_ok == True:
            result = ast.literal_eval(json.loads(response.content))

            name_list = list(result)

            return name_list

    def get_basic_hk_stock_info(self):

        link_url = 'http://www.hkfdb.net/data_api?'
        token_str = 'token=' + str(self.authToken)
        database_str = 'database=' + 'basic_hk_stock_info'
        link_str = link_url + '&' + token_str + '&' + database_str

        response = requests.get(link_str)
        response_ok = response_check(response)
        if response_ok == True:

            r_content = response.content
            json1 = json.loads(r_content).replace("'", "\"")
            json1 = json1.replace('nan', 'NaN')
            json1 = json1.replace('INT\"L', 'INTL')
            json1 = json1.replace('L\"OCCITANE', 'LOCCITANE')
            json1 = json1.replace('True', '\"True\"')
            json1 = json1.replace('False', '\"False\"')
            json1 = json1.replace('\"\"True\"\"', '\"True\"')
            json1 = json1.replace('\"\"False\"\"', '\"False\"')

            result = json.loads(json1)

            df = pd.DataFrame(result)

            if '-' in df.at[0, 'ipo_date']:
                df['ipo_date'] = pd.to_datetime(df['ipo_date'], format='%Y-%m-%d')
            else:
                df['ipo_date'] = pd.to_datetime(df['ipo_date'], format='%Y%m%d')

            df['share_issued'] = df['share_issued'].astype(str)
            df['share_issued'] = df['share_issued'].str.replace('-', '', regex=False)
            df['share_issued'] = df['share_issued'].astype('float')

            df['volume'] = df['volume'].str.replace('.0', '', regex=False)
            df['turnover'] = df['turnover'].str.replace('.0', '', regex=False)
            df['market_capital'] = df['market_capital'].str.replace('.0', '', regex=False)

            df = df.sort_values(by='code')

            df['market_capital'] = df['market_capital'].astype('int64')
            df['is_stop_trading'] = df['is_stop_trading'].map({'True': True, 'False': False})
            df = df.rename(columns={'is_stop_trading': 'stop_trading'})

            float_col_list = ['price', 'PE', 'EPS', 'dividend']
            int_col_list = ['volume', 'turnover']
            for col in float_col_list:
                df[col] = df[col].str.replace('-', '', regex=False)
                df[col] = df[col].str.replace('.000', '', regex=False)
                df[col] = df[col].str.replace(',', '', regex=False)
                df[col] = df[col].astype(float)

            for col in int_col_list:
                df[col] = df[col].astype('int64')
            df['lot_size'] = df['lot_size'].astype(float)

            df = df[['code', 'stock_name', 'price', 'PE', 'EPS', 'dividend', 'volume', 'turnover', 'share_issued',
                     'lot_size', 'market_capital', 'ipo_date', 'year_end_date', 'stop_trading', 'category']]
            return df

    def get_hk_ipo_hist(self):

        link_url = 'http://www.hkfdb.net/data_api?'
        token_str = 'token=' + str(self.authToken)
        database_str = 'database=' + 'hk_ipo_hist'
        link_str = link_url + '&' + token_str + '&' + database_str

        response = requests.get(link_str)
        response_ok = response_check(response)
        if response_ok == True:

            json_content = json.loads(response.content)
            json_content = json_content.replace(' nan', '\" nan\"')
            json_content = json_content.replace('N/A\\n\\n', '0')
            json_content = json_content.replace('N/A\\n', '0')
            json_content = json_content.replace('0\\n', '0')

            result = ast.literal_eval(json_content)

            df = pd.DataFrame(result)
            col_list = ['name', 'sponsors', 'accountants', 'valuers']

            for col in col_list:
                df[col] = df[col].str.replace('\n', ' ', regex=False)
            for col in col_list:
                for i in range(len(df)):
                    content = df.loc[i, col]
                    if content[-1] == ' ':
                        df.at[i, col] = content[0:-1]
                    if 'Appraisaland' in content:
                        df.at[i, col] = content.replace('Appraisaland', 'Appraisal and')

            # df['prospectus_date'] = pd.to_datetime(df['prospectus_date'], format='%d/%m/%Y')
            # df['listing_date'] = pd.to_datetime(df['listing_date'], format='%d/%m/%Y')

            return df

    def get_market_highlight(self, start_date, end_date):

        market = 'hk_main_board'

        check_bool_dict = self.check_market_highlight_args(market, start_date, end_date)

        if False not in list(check_bool_dict.values()):
            link_url = 'http://www.hkfdb.net/data_api?'
            token_str = 'token=' + str(self.authToken)
            database_str = 'database=' + 'market_highlight'
            market_str = 'market=' + market
            start_date_str = 'start_date=' + str(start_date)
            end_date_str = 'end_date=' + str(end_date)
            link_str = link_url + market_str + '&' + token_str + '&' + database_str + '&' + start_date_str + '&' + \
                       end_date_str

            response = requests.get(link_str)
            response_ok = response_check(response)
            if response_ok == True:

                result = json.loads(json.loads(response.content).replace("'", "\""))

                df_list = []
                for item in result:
                    date_int = item['_id']
                    df = pd.DataFrame(item['content'])
                    if len(df) > 0:
                        df['date'] = str(date_int)
                        df_list.append(df)
                df = pd.concat(df_list)

                df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
                df = df.drop_duplicates(subset='date', keep='last')
                df = df.set_index(keys='date')
                df = df.sort_index()

                df = df.rename(columns={'average_pe_ratio_times': 'average_pe_ratio'})

                return df

        else:
            err_msg = 'Error in: '
            for error in check_bool_dict:
                if check_bool_dict[error] == False:
                    err_msg += error + ','
            print(err_msg)

    def get_north_water(self, start_date, end_date):

        check_bool_dict = self.check_start_end_date(start_date, end_date)

        if False not in list(check_bool_dict.values()):
            link_url = 'http://www.hkfdb.net/data_api?'
            token_str = 'token=' + str(self.authToken)
            database_str = 'database=' + 'north_water'
            start_date_str = 'start_date=' + str(start_date)
            end_date_str = 'end_date=' + str(end_date)
            link_str = link_url + '&' + token_str + '&' + database_str + '&' + start_date_str + '&' + \
                       end_date_str

            response = requests.get(link_str)
            response_ok = response_check(response)
            if response_ok == True:

                json_content = json.loads(response.content)
                if 'nan' in json_content:
                    result = json.loads(json_content.replace("'", "\"").replace("nan", "0"))
                else:
                    result = json.loads(json_content.replace("'", "\""))

                df_list = []
                for item in result:
                    date_int = item['_id']
                    df = pd.DataFrame(item['content'])
                    if len(df) > 0:
                        df['date'] = str(date_int)
                        df_list.append(df)
                df = pd.concat(df_list)

                df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')

                df = df.set_index(keys='date')
                df = df.sort_index()
                for col in df.columns:
                    df[col] = df[col].astype(int)

                return df

        else:
            err_msg = 'Error in: '
            for error in check_bool_dict:
                if check_bool_dict[error] == False:
                    err_msg += error + ','
            print(err_msg)

    def get_hk_deri_daily_market_report(self, deri, code, start_date, end_date, exp='current'):

        check_bool_dict = self.check_hk_deri_daily_market_report_args(deri, code, start_date, end_date, exp)

        if False not in list(check_bool_dict.values()):
            link_url = 'http://www.hkfdb.net/data_api?'
            token_str = 'token=' + str(self.authToken)
            deri_str = 'deri=' + deri
            code_str = 'code=' + code
            exp_str = 'exp=' + exp
            database_str = 'database=' + 'hk_deri_daily_market_report'
            start_date_str = 'start_date=' + str(start_date)
            end_date_str = 'end_date=' + str(end_date)
            link_str = link_url + '&' + token_str + '&' + database_str \
                       + '&' + start_date_str + '&' + end_date_str \
                       + '&' + deri_str + '&' + code_str + '&' + exp_str

            response = requests.get(link_str)
            response_ok = response_check(response)
            if response_ok == True:

                result = json.loads(json.loads(response.content).replace("'", "\""))

                df_list = []

                for item in result:
                    date_int = item['_id']
                    df = pd.DataFrame(item['content'])
                    if len(df) > 0:
                        df['date'] = str(date_int)
                        df_list.append(df)
                df = pd.concat(df_list)

                df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')

                if deri == 'opt':
                    df = df.rename(columns={'contract_month': 'year_month'})
                    df['year_month'] = df['year_month'].str.replace('-', '', regex=False)

                    if 'wo' in code:
                        df['year_month'] = pd.to_datetime(df['year_month'], format='%d%b%y')
                        df = df.sort_values(by=['date', 'year_month'])
                        df['year_month'] = df['year_month'].dt.strftime('%d%b%y')
                    else:
                        df5 = df[df['year_month'].str.len() == 5].copy()
                        df5['year_month'] = pd.to_datetime(df5['year_month'], format='%b%y')
                        df7 = df[df['year_month'].str.len() == 7].copy()
                        df7['year_month'] = pd.to_datetime(df7['year_month'], format='%d%b%y')

                        df = pd.concat([df5, df7])

                        df = df.sort_values(by=['date', 'year_month'])
                        df['year_month'] = df['year_month'].dt.strftime('%b-%y')

                    if code.isdigit() == True:
                        cols = list(df.columns)
                        cols = [cols[-1]] + cols[:-1]
                        df = df[cols]
                    df = df.reset_index(drop=True)

                elif deri == 'fut':
                    df = df.sort_values(by='date')
                    df = df.set_index('date')

                if 'strike_price' in df.columns:
                    df = df.rename(columns={'strike_price': 'strike'})
                if 'change_in_settlement' in df.columns:
                    df = df.rename(columns={'change_in_settlement': 'close_change'})
                if 'year_month' in df.columns:
                    df = df.rename(columns={'year_month': 'contract_month'})
                if 'volumne' in df.columns:
                    df = df.rename(columns={'volumne': 'volume'})

                return df

        else:
            err_msg = 'Error in: '
            for error in check_bool_dict:
                if check_bool_dict[error] == False:
                    err_msg += error + ','
            print(err_msg)

    def get_hk_cbbc(self, code, start_date, end_date):

        check_bool_dict = self.check_hk_cbbc(code, start_date, end_date)

        if False not in list(check_bool_dict.values()):
            link_url = 'http://www.hkfdb.net/data_api?'
            token_str = 'token=' + str(self.authToken)
            code_str = 'code=' + code
            database_str = 'database=' + 'hk_cbbc'
            start_date_str = 'start_date=' + str(start_date)
            end_date_str = 'end_date=' + str(end_date)
            link_str = link_url + '&' + token_str + '&' + database_str \
                       + '&' + start_date_str + '&' + end_date_str + '&' + code_str

            response = requests.get(link_str)
            response_ok = response_check(response)
            if response_ok == True:

                result_list = json.loads(json.loads(response.content).replace("'", "\""))

                columns = ['unique_id', 'cbbc_code', 'cbbc_name', 'date', 'num_of_cbbc_bought',
                           'avg_price_per_cbbc_bought',
                           'num_of_cbbc_sold', 'avg_price_per_cbbc_sold', 'num_of_cbbc_in_mkt', 'total_issued_size',
                           'currency', 'issuer', 'underlying', 'bull_bear', 'listing_date', 'strike_or_call_currency',
                           'strike_level', 'call_level', 'entitlement_ratio']

                df_list = []
                for result in result_list:
                    for item, content in result.items():
                        if type(content) is list:
                            df = pd.DataFrame(content, columns=columns)
                            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
                            df['listing_date'] = pd.to_datetime(df['listing_date'], format='%Y%m%d')
                            df_list.append(df)

                df = pd.concat(df_list)
                df = df.sort_values('date')
                df['num_of_cbbc_sold'] = df['num_of_cbbc_sold'].abs()
                df['avg_price_per_cbbc_sold'] = df['avg_price_per_cbbc_sold'].abs()
                df['bull_bear'] = df['bull_bear'].str.replace(' ', '')
                df = df.set_index('unique_id')
                # df = df.drop('index', axis=1)

                return df

        else:
            err_msg = 'Error in: '
            for error in check_bool_dict:
                if check_bool_dict[error] == False:
                    err_msg += error + ','
            print(err_msg)

    #########################################################################################

    def check_hk_stock_ohlc_args(self, code, start_date, end_date, freq):
        freq_list = ['1T', '5T', '15T', '30T', '1D', '1DW']
        freq_valid = True if freq in freq_list else False

        try:
            code_length = len(code) == 5
        except:
            code_length = False
        try:
            code_isdigit = code.isdigit() == True
        except:
            code_isdigit = False
        try:
            start_date_is_int = isinstance(start_date, int)
        except:
            start_date_is_int = False
        try:
            start_date_length = len(str(start_date)) == 8
        except:
            start_date_length = False
        try:
            start_date_future = datetime.datetime.strptime(str(start_date),
                                                           '%Y%m%d').date() <= datetime.datetime.now().date()
        except:
            start_date_future = False
        try:
            end_date_is_int = isinstance(end_date, int)
        except:
            end_date_is_int = False
        try:
            end_date_length = len(str(end_date)) == 8
        except:
            end_date_length = False

        # try:
        #     end_date_future = datetime.datetime.strptime(str(end_date),
        #                                                  '%Y%m%d').date() <= datetime.datetime.now().date()
        # except:
        #     end_date_future = False

        try:
            end_after_start_date = datetime.datetime.strptime(str(end_date), '%Y%m%d').date() >= \
                                   datetime.datetime.strptime(str(start_date), '%Y%m%d').date()
        except:
            end_after_start_date = False

        check_bool_dict = {'freq_valid': freq_valid,
                           'code_isdigit': code_isdigit,
                           'code_length': code_length,
                           'start_date_length': start_date_length,
                           'start_date_is_int': start_date_is_int,
                           'start_date_future': start_date_future,
                           'end_date_is_int': end_date_is_int,
                           'end_date_length': end_date_length,
                           # 'end_date_future': end_date_future,
                           'end_after_start_date': end_after_start_date}

        return check_bool_dict

    def check_us_stock_ohlc_args(self, code, start_date, end_date):

        try:
            code_length = len(code) > 0
        except:
            code_length = False

        try:
            start_date_is_int = isinstance(start_date, int)
        except:
            start_date_is_int = False
        try:
            start_date_length = len(str(start_date)) == 8
        except:
            start_date_length = False
        try:
            start_date_future = datetime.datetime.strptime(str(start_date),
                                                           '%Y%m%d').date() <= datetime.datetime.now().date()
        except:
            start_date_future = False
        try:
            end_date_is_int = isinstance(end_date, int)
        except:
            end_date_is_int = False
        try:
            end_date_length = len(str(end_date)) == 8
        except:
            end_date_length = False
        # try:
        #     end_date_future = datetime.datetime.strptime(str(end_date),
        #                                                  '%Y%m%d').date() <= datetime.datetime.now().date()
        # except:
        #     end_date_future = False
        try:
            end_after_start_date = datetime.datetime.strptime(str(end_date),
                                                              '%Y%m%d').date() >= datetime.datetime.strptime(
                str(start_date), '%Y%m%d').date()
        except:
            end_after_start_date = False

        check_bool_dict = {'code_length': code_length,
                           'start_date_length': start_date_length,
                           'start_date_is_int': start_date_is_int,
                           'start_date_future': start_date_future,
                           'end_date_is_int': end_date_is_int,
                           'end_date_length': end_date_length,
                           # 'end_date_future': end_date_future,
                           'end_after_start_date': end_after_start_date}

        return check_bool_dict

    def check_hk_fut_ohlc_args(self, index, freq, start_date, end_date, rolling_day, rolling_time):

        freq_list = ['1T', '5T', '15T', '1D']
        freq_valid = True if freq in freq_list else False

        try:
            index_name = (index == 'HSI') or (index == 'HHI') or (index == 'HTI')
        except:
            index_name = False
        try:
            start_date_is_int = isinstance(start_date, int)
        except:
            start_date_is_int = False
        try:
            start_date_length = len(str(start_date)) == 8
        except:
            start_date_length = False
        try:
            start_date_future = datetime.datetime.strptime(str(start_date),
                                                           '%Y%m%d').date() <= datetime.datetime.now().date()
        except:
            start_date_future = False
        try:
            end_date_is_int = isinstance(end_date, int)
        except:
            end_date_is_int = False
        try:
            end_date_length = len(str(end_date)) == 8
        except:
            end_date_length = False
        # try:
        #     end_date_future = datetime.datetime.strptime(str(end_date),
        #                                                  '%Y%m%d').date() <= datetime.datetime.now().date()
        # except:
        #     end_date_future = False
        try:
            end_after_start_date = datetime.datetime.strptime(str(end_date),
                                                              '%Y%m%d').date() >= datetime.datetime.strptime(
                str(start_date), '%Y%m%d').date()
        except:
            end_after_start_date = False

        try:
            rolling_day_int = isinstance(rolling_day, int)
        except:
            rolling_day_int = False
        try:
            rolling_day_length = rolling_day <= 5
        except:
            rolling_day_length = False
        try:
            rolling_time_int = isinstance(rolling_time, int)
        except:
            rolling_time_int = False

        check_bool_dict = {'index_name': index_name,
                           'freq_valid': freq_valid,
                           'start_date_length': start_date_length,
                           'start_date_is_int': start_date_is_int,
                           'start_date_future': start_date_future,
                           'end_date_is_int': end_date_is_int,
                           'end_date_length': end_date_length,
                           # 'end_date_future': end_date_future,
                           'end_after_start_date': end_after_start_date,
                           'rolling_day_int': rolling_day_int,
                           'rolling_day_length': rolling_day_length,
                           'rolling_time_int': rolling_time_int}

        return check_bool_dict

    def check_market_highlight_args(self, market, start_date, end_date):
        try:
            market_length = len(market) > 0
        except:
            market_length = False
        try:
            start_date_is_int = isinstance(start_date, int)
        except:
            start_date_is_int = False
        try:
            start_date_length = len(str(start_date)) == 8
        except:
            start_date_length = False
        try:
            start_date_future = datetime.datetime.strptime(str(start_date),
                                                           '%Y%m%d').date() <= datetime.datetime.now().date()
        except:
            start_date_future = False
        try:
            end_date_is_int = isinstance(end_date, int)
        except:
            end_date_is_int = False
        try:
            end_date_length = len(str(end_date)) == 8
        except:
            end_date_length = False
        # try:
        #     end_date_future = datetime.datetime.strptime(str(end_date),
        #                                                  '%Y%m%d').date() <= datetime.datetime.now().date()
        # except:
        #     end_date_future = False
        try:
            end_after_start_date = datetime.datetime.strptime(str(end_date),
                                                              '%Y%m%d').date() >= datetime.datetime.strptime(
                str(start_date), '%Y%m%d').date()
        except:
            end_after_start_date = False

        check_bool_dict = {'market_length': market_length,
                           'start_date_length': start_date_length,
                           'start_date_is_int': start_date_is_int,
                           'start_date_future': start_date_future,
                           'end_date_is_int': end_date_is_int,
                           'end_date_length': end_date_length,
                           # 'end_date_future': end_date_future,
                           'end_after_start_date': end_after_start_date}
        return check_bool_dict

    def check_start_end_date(self, start_date, end_date):

        try:
            start_date_is_int = isinstance(start_date, int)
        except:
            start_date_is_int = False
        try:
            start_date_length = len(str(start_date)) == 8
        except:
            start_date_length = False
        try:
            start_date_future = datetime.datetime.strptime(str(start_date),
                                                           '%Y%m%d').date() <= datetime.datetime.now().date()
        except:
            start_date_future = False
        try:
            end_date_is_int = isinstance(end_date, int)
        except:
            end_date_is_int = False
        try:
            end_date_length = len(str(end_date)) == 8
        except:
            end_date_length = False
        # try:
        #     end_date_future = datetime.datetime.strptime(str(end_date),
        #                                                  '%Y%m%d').date() <= datetime.datetime.now().date()
        # except:
        #     end_date_future = False
        try:
            end_after_start_date = datetime.datetime.strptime(str(end_date),
                                                              '%Y%m%d').date() >= datetime.datetime.strptime(
                str(start_date), '%Y%m%d').date()
        except:
            end_after_start_date = False

        check_bool_dict = {
            'start_date_length': start_date_length,
            'start_date_is_int': start_date_is_int,
            'start_date_future': start_date_future,
            'end_date_is_int': end_date_is_int,
            'end_date_length': end_date_length,
            # 'end_date_future': end_date_future,
            'end_after_start_date': end_after_start_date}

        return check_bool_dict

    def check_ccass_by_id_args(self, ccass_id, start_date, end_date):
        if len(ccass_id) > 0:
            ccass_id_len = True
        else:
            ccass_id_len = False
        try:
            start_date_is_int = isinstance(start_date, int)
        except:
            start_date_is_int = False
        try:
            start_date_length = len(str(start_date)) == 8
        except:
            start_date_length = False
        try:
            start_date_future = datetime.datetime.strptime(str(start_date),
                                                           '%Y%m%d').date() <= datetime.datetime.now().date()
        except:
            start_date_future = False
        try:
            end_date_is_int = isinstance(end_date, int)
        except:
            end_date_is_int = False
        try:
            end_date_length = len(str(end_date)) == 8
        except:
            end_date_length = False
        # try:
        #     end_date_future = datetime.datetime.strptime(str(end_date), '%Y%m%d').date() <= datetime.datetime.now().date()
        # except:
        #     end_date_future = False
        try:
            end_after_start_date = datetime.datetime.strptime(str(end_date),
                                                              '%Y%m%d').date() >= datetime.datetime.strptime(
                str(start_date), '%Y%m%d').date()
        except:
            end_after_start_date = False

        check_bool_dict = {'ccass_id_len': ccass_id_len,
                           'start_date_length': start_date_length,
                           'start_date_is_int': start_date_is_int,
                           'start_date_future': start_date_future,
                           'end_date_is_int': end_date_is_int,
                           'end_date_length': end_date_length,
                           # 'end_date_future': end_date_future,
                           'end_after_start_date': end_after_start_date}
        return check_bool_dict

    def check_ccass_by_code_args(self, code, start_date, end_date):

        try:
            code_length = len(code) == 5
        except:
            code_length = False
        try:
            code_isdigit = code.isdigit() == True
        except:
            code_isdigit = False
        try:
            start_date_is_int = isinstance(start_date, int)
        except:
            start_date_is_int = False
        try:
            start_date_length = len(str(start_date)) == 8
        except:
            start_date_length = False
        try:
            start_date_future = datetime.datetime.strptime(str(start_date),
                                                           '%Y%m%d').date() <= datetime.datetime.now().date()
        except:
            start_date_future = False
        try:
            end_date_is_int = isinstance(end_date, int)
        except:
            end_date_is_int = False
        try:
            end_date_length = len(str(end_date)) == 8
        except:
            end_date_length = False
        # try:
        #     end_date_future = datetime.datetime.strptime(str(end_date),
        #                                                  '%Y%m%d').date() <= datetime.datetime.now().date()
        # except:
        #     end_date_future = False
        try:
            end_after_start_date = datetime.datetime.strptime(str(end_date),
                                                              '%Y%m%d').date() >= datetime.datetime.strptime(
                str(start_date), '%Y%m%d').date()
        except:
            end_after_start_date = False

        check_bool_dict = {
            'code_isdigit': code_isdigit,
            'code_length': code_length,
            'start_date_length': start_date_length,
            'start_date_is_int': start_date_is_int,
            'start_date_future': start_date_future,
            'end_date_is_int': end_date_is_int,
            'end_date_length': end_date_length,
            # 'end_date_future': end_date_future,
            'end_after_start_date': end_after_start_date}

        return check_bool_dict

    def check_ccass_holding_rank_args(self, code, start_date, end_date):

        try:
            code_length = len(code) == 5
        except:
            code_length = False
        try:
            code_isdigit = code.isdigit() == True
        except:
            code_isdigit = False
        try:
            start_date_is_int = isinstance(start_date, int)
        except:
            start_date_is_int = False
        try:
            start_date_length = len(str(start_date)) == 8
        except:
            start_date_length = False
        try:
            start_date_future = datetime.datetime.strptime(str(start_date),
                                                           '%Y%m%d').date() <= datetime.datetime.now().date()
        except:
            start_date_future = False

        try:
            end_date_is_int = isinstance(end_date, int)
        except:
            end_date_is_int = False
        try:
            end_date_length = len(str(end_date)) == 8
        except:
            end_date_length = False
        # try:
        #     end_date_future = datetime.datetime.strptime(str(end_date),
        #                                                  '%Y%m%d').date() <= datetime.datetime.now().date()
        # except:
        #     end_date_future = False
        try:
            end_after_start_date = datetime.datetime.strptime(str(end_date),
                                                              '%Y%m%d').date() >= datetime.datetime.strptime(
                str(start_date), '%Y%m%d').date()
        except:
            end_after_start_date = False

        check_bool_dict = {
            'code_isdigit': code_isdigit,
            'code_length': code_length,
            'start_date_length': start_date_length,
            'start_date_is_int': start_date_is_int,
            'start_date_future': start_date_future,
            'end_date_is_int': end_date_is_int,
            'end_date_length': end_date_length,
            # 'end_date_future': end_date_future,
            'end_after_start_date': end_after_start_date}

        return check_bool_dict

    def check_hk_deri_daily_market_report_args(self, deri, code, start_date, end_date, exp):

        if deri == 'fut':
            deri_type = True
        elif deri == 'opt':
            deri_type = True
        else:
            deri_type = False

        if exp == 'current':
            exp_type = True
        elif exp == 'next':
            exp_type = True
        else:
            exp_type = False

        try:
            code_length = len(code) > 0
        except:
            code_length = False
        try:
            start_date_is_int = isinstance(start_date, int)
        except:
            start_date_is_int = False
        try:
            start_date_length = len(str(start_date)) == 8
        except:
            start_date_length = False
        try:
            start_date_future = datetime.datetime.strptime(str(start_date),
                                                           '%Y%m%d').date() <= datetime.datetime.now().date()
        except:
            start_date_future = False
        try:
            end_date_is_int = isinstance(end_date, int)
        except:
            end_date_is_int = False
        try:
            end_date_length = len(str(end_date)) == 8
        except:
            end_date_length = False
        # try:
        #     end_date_future = datetime.datetime.strptime(str(end_date),
        #                                                  '%Y%m%d').date() <= datetime.datetime.now().date()
        # except:
        #     end_date_future = False
        try:
            end_after_start_date = datetime.datetime.strptime(str(end_date),
                                                              '%Y%m%d').date() >= datetime.datetime.strptime(
                str(start_date), '%Y%m%d').date()
        except:
            end_after_start_date = False

        check_bool_dict = {'code_length': code_length,
                           'start_date_length': start_date_length,
                           'start_date_is_int': start_date_is_int,
                           'start_date_future': start_date_future,
                           'end_date_is_int': end_date_is_int,
                           'end_date_length': end_date_length,
                           # 'end_date_future': end_date_future,
                           'end_after_start_date': end_after_start_date,
                           'deri_type': deri_type,
                           'exp_type': exp_type}

        return check_bool_dict

    def check_hk_cbbc(self, code, start_date, end_date):

        try:
            code_length = len(code) > 0
        except:
            code_length = False
        try:
            start_date_is_int = isinstance(start_date, int)
        except:
            start_date_is_int = False
        try:
            start_date_length = len(str(start_date)) == 8
        except:
            start_date_length = False
        try:
            end_date_is_int = isinstance(end_date, int)
        except:
            end_date_is_int = False
        try:
            end_date_length = len(str(end_date)) == 8
        except:
            end_date_length = False

        check_bool_dict = {'code_length': code_length,
                           'start_date_length': start_date_length,
                           'start_date_is_int': start_date_is_int,
                           'end_date_is_int': end_date_is_int,
                           'end_date_length': end_date_length, }

        return check_bool_dict

    def check_hk_code_args(self, code):

        try:
            code_length = len(code) > 0
        except:
            code_length = False
        try:
            code_isdigit = code.isdigit()
        except:
            code_isdigit = False

        check_bool_dict = {'code_length': code_length,
                           'code_isdigit': code_isdigit}

        return check_bool_dict


################################ other tools ################################

def get_holiday_from_gov(year):
    r = requests.get('https://www.gov.hk/en/about/abouthk/holiday/' + year + '.htm')
    soup = BeautifulSoup(r.content.decode('utf-8'), 'lxml')
    items = soup.find('table').find_all('tr')

    holiday_date_list = []
    half_day_mkt_date_list = []

    for item in items[1:]:
        tds = item.find_all('td')
        holiday_date = tds[1].text + ' ' + year
        holiday_date = datetime.datetime.strptime(holiday_date, '%d %B %Y').date()
        holiday_name = tds[0].text.lower()
        holiday_date_list.append(holiday_date)
        if 'lunar new year' in holiday_name and 'the' not in holiday_name:
            lin30_date = holiday_date - datetime.timedelta(days=1)
            half_day_mkt_date_list.append(lin30_date)

    xmax_eva_date = datetime.date(int(year), 12, 24)
    if xmax_eva_date.weekday() < 5:
        half_day_mkt_date_list.append(xmax_eva_date)

    xmax_eva_date = datetime.date(int(year), 12, 24)
    if xmax_eva_date.weekday() < 5:
        half_day_mkt_date_list.append(xmax_eva_date)
    year_eva_date = datetime.date(int(year), 12, 31)
    if year_eva_date.weekday() < 5:
        half_day_mkt_date_list.append(year_eva_date)

    return holiday_date_list, half_day_mkt_date_list


def get_hk_holiday_and_expiry_date(start_year, end_year, format='int', str_format='%Y%m%d'):
    holiday_date_list = []
    half_day_mkt_date_list = []

    for i in range(end_year - start_year + 1):
        this_year = end_year - i
        this_year_str = str(this_year)
        new_holiday_date_list, new_half_day_mkt_date_list = get_holiday_from_gov(this_year_str)
        holiday_date_list = holiday_date_list + new_holiday_date_list
        half_day_mkt_date_list = half_day_mkt_date_list + new_half_day_mkt_date_list

    start_date = datetime.date(start_year, 1, 1)
    end_date = datetime.date(end_year, 12, 31)
    date_diff = (end_date - start_date).days

    expiry_date_list = []
    for i in range(date_diff):
        date = end_date - datetime.timedelta(days=i)
        last_date = date + datetime.timedelta(days=1)
        if last_date.day == 1:
            trading_days = 0
            for j in range(7):
                test_date = date - datetime.timedelta(days=j)
                if test_date.weekday() < 5 and test_date not in holiday_date_list:
                    trading_days += 1
                if trading_days == 2:
                    if format == 'str' or format == 'string':
                        expiry_date = test_date.strftime(str_format)
                    elif format == 'int' or format == 'integer':
                        expiry_date = int(test_date.strftime('%Y%m%d'))
                    elif format == 'dt' or format == 'datetime':
                        expiry_date = test_date
                    expiry_date_list.append(expiry_date)
                    break

    holiday_list = []
    for day in holiday_date_list:
        if format == 'str' or format == 'string':
            holiday = day.strftime(str_format)
        elif format == 'int' or format == 'integer':
            holiday = int(day.strftime('%Y%m%d'))
        elif format == 'dt' or format == 'datetime':
            holiday = day
        holiday_list.append(holiday)

    half_day_mkt_list = []
    for day in half_day_mkt_date_list:
        if format == 'str' or format == 'string':
            holiday = day.strftime(str_format)
        elif format == 'int' or format == 'integer':
            holiday = int(day.strftime('%Y%m%d'))
        elif format == 'dt' or format == 'datetime':
            holiday = day
        half_day_mkt_list.append(holiday)

    dict1 = {'expiry_date': expiry_date_list, 'public_holiday': holiday_list, 'half_day_mkt': half_day_mkt_list}
    return dict1


def get_current_us_holiday(format='int', str_format='%Y%m%d'):
    url = 'https://www.nasdaqtrader.com/Trader.aspx?id=Calendar'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) \
        Chrome/86.0.4240.193 Safari/537.36'}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    text = r.text

    soup = BeautifulSoup(text, 'lxml')

    ths = soup.find('table').find_all('th')
    cols = []
    for th in ths:
        text = th.text
        cols.append(text)

    data = []
    trs = soup.find('table').find_all('tr')
    for tr in trs:
        info = []
        tds = tr.find_all('td')
        for td in tds:
            text = td.text
            info.append(text)
        if len(info) > 0:
            data.append(info)
    df = pd.DataFrame(data)
    df.columns = ['date', 'holiday', 'status']
    df = df.loc[df['status'] == 'Closed']

    us_holiday_list = []
    date_list = df['date'].to_list()
    for holiday in date_list:
        if format == 'dt':
            us_holiday_list.append(datetime.datetime.strptime(holiday, '%B %d, %Y').date())
        elif format == 'str':
            us_holiday_list.append(datetime.datetime.strptime(holiday, '%B %d, %Y').strftime(str_format))
        elif format == 'int':
            us_holiday_list.append(int(datetime.datetime.strptime(holiday, '%B %d, %Y').strftime(str_format)))

    return us_holiday_list


def response_check(response):
    response_ok = True

    if response.status_code == 200:
        response_string = response.content.decode('utf-8')
        response_dict = json.loads(response_string)
        if 'Content' in response_dict:
            if response_dict['Content'] == 'Token Error':
                print('Token Error, please check for token or payment issues')
                response_ok = False
            if response_dict['State'] == 400:
                response_ok = False
    else:
        print('Connection Error, please check pc internet setting')
        response_ok = False

    return response_ok


def get_stock_tick_size(market, price):
    if market == 'HK':
        if price >= 0.01 and price < 0.25:
            tick_size = 0.001
        elif price >= 0.25 and price < 0.5:
            tick_size = 0.005
        elif price >= 0.5 and price < 10:
            tick_size = 0.01
        elif price >= 10 and price < 20:
            tick_size = 0.02
        elif price >= 20 and price < 100:
            tick_size = 0.05
        elif price >= 100 and price < 200:
            tick_size = 0.1
        elif price >= 200 and price < 500:
            tick_size = 0.2
        elif price >= 500 and price < 1000:
            tick_size = 0.5
        elif price >= 1000 and price < 2000:
            tick_size = 1
        elif price >= 2000 and price < 5000:
            tick_size = 2
        elif price >= 5000 and price < 9995:
            tick_size = 5

    elif market == 'US':
        if price < 1:
            tick_size = 0.0001
        else:
            tick_size = 0.001

    return tick_size