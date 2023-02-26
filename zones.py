import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import binance.spot as bn
import pandas as pd
import time
from datetime import datetime


def convert_timeframe(timeframe_string: str) -> int:
    """
    Converts timeframe strings into milliseconds

    Args:
        timeframe_string (str): 1m, 30m, 1h, 4h, 1d, 1w, etc.

    Returns:
        timeframe_ms (int): 1m -> 60 * 1000 = 60000, 1h -> 60 * 60 * 1000 = 3600000
    """
    unit = timeframe_string[-1]
    try:
        number = int(timeframe_string[:-1])
        if unit == "m":
            timeframe_ms = number * 60000
        elif unit == "h":
            timeframe_ms = number * 60000 * 60
        elif unit == "d":
            timeframe_ms = number * 60000 * 60 * 24
        elif unit == "w":
            timeframe_ms = number * 60000 * 60 * 24 * 7
        else:
            timeframe_ms = 0
    except:
        timeframe_ms = 0
    return timeframe_ms


def get_table(client: bn.Spot, symbol: str, last_time: int, timeframe_str: str, timeframe_ms: int) -> pd.DataFrame:
    """
    gets price candles for given symbol in given period and timeframe (gets 1000 candles max)

    Args:
        client (bn.Spot): Binance connector spot client object
        symbol (str): A trading pair in Binance exchange (e.g. "BTCUSDT", "UNIBTC")
        last_time (int): Unix timestamp for the last candle
        timeframe_str (str): 1m, 30m, 1h, 4h, 1d, 1w, etc.
        timeframe_ms (int): 1m -> 60 * 1000 = 60000, 1h -> 60 * 60 * 1000 = 3600000

    Returns:
        Pandas Dataframe object with columns: 
            "open_timestamp", "open", "high", "low", "close", "volume",
            "close_timestamp", "qvolume", "trades_number",
            "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"
    """
    try:
        starttime = last_time - timeframe_ms * 1000
        table = client.klines(symbol, timeframe_str, startTime=starttime, endTime=last_time + 1, limit=1000)

        if len(table) > 0:
            data = pd.DataFrame(table, columns=["open_timestamp", "open", "high", "low", "close", "volume",
                                                "close_timestamp", "qvolume", "trades_number",
                                                "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"])
            return data
        else:
            return pd.DataFrame(columns=["open_timestamp", "open", "high", "low", "close", "volume",
                                         "close_timestamp", "qvolume", "trades_number", "taker_buy_base_volume",
                                         "taker_buy_quote_volume", "ignore"])
    except:
        print("error getting table!")
        time.sleep(3)
        return get_table(client, symbol, last_time, timeframe_str, timeframe_ms)


def get_candles(symbol: str, start_time: int, timeframe_str: str) -> pd.DataFrame:
    """
    Gets all available price candles in a given timeframe for a given symbol from a given time until now 

    Args:
        symbol (str): A trading pair in Binance exchange (e.g. "BTCUSDT", "UNIBTC")
        start_time (int): Open timestamp of the first price candle it gets in Unix format
        timeframe_str (str): 1m, 30m, 1h, 4h, 1d, 1w, etc.

    Returns:
        Pandas Dataframe object with columns: 
            "open_timestamp", "open", "high", "low", "close", "volume",
            "close_timestamp", "qvolume", "trades_number",
            "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"
    """
    timeframe_ms = convert_timeframe(timeframe_str)
    client = bn.Spot()
    current_timestamp = int(datetime.now().timestamp()*1000)
    last_timestamp_in_timeframe = current_timestamp - \
        (current_timestamp % timeframe_ms)
    candles_df = pd.DataFrame(columns=["open_timestamp", "open", "high", "low", "close", "volume",
                                       "close_timestamp", "qvolume", "trades_number", "taker_buy_base_volume",
                                       "taker_buy_quote_volume", "ignore"])
    for last_time in range(last_timestamp_in_timeframe, start_time, -timeframe_ms * 1000):
        data = get_table(client, symbol, last_time,
                         timeframe_str, timeframe_ms)
        candles_df = pd.concat([candles_df, data], axis=0)
    candles_df = candles_df.sort_values(
        by="open_timestamp", ascending=True, ignore_index=True)
    candles_df = candles_df.astype(float)
    return candles_df


def generate_missing_candles(data: pd.DataFrame) -> pd.DataFrame:
    """
    Drops extra columns and finds missing candles in dataframe and generates them

    Args:
        data: Pandas Dataframe object with columns: 
            "open_timestamp", "open", "high", "low", "close", "volume",
            "close_timestamp", "qvolume", "trades_number",
            "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"

    Returns:
        Pandas Dataframe object with columns: 
            "open_timestamp", "open", "high", "low", "close", "volume",
            "close_timestamp", "trades_number"
    """
    data = data.drop(axis="columns",
                    labels=["qvolume", "taker_buy_base_volume",
                            "taker_buy_quote_volume", "ignore"])

    for index in range(1, len(data)):
        if data["close_timestamp"][index - 1] + 1 != data["open_timestamp"][index]:
            open_timestamp = data["close_timestamp"][index - 1] + 1
            open_price = data["close"][index - 1]
            close_price = data["open"][index]
            high_price = max(open_price, close_price)
            low_price = min(open_price, close_price)
            volume = sum([data["volume"][index - 1], data["volume"][index]]) / 2
            close_timestamp = data["open_timestamp"][index] - 1
            trades_number = sum([data["trades_number"][index - 1],
                                data["trades_number"][index]]) / 2
            new_row = pd.DataFrame([[open_timestamp, open_price, high_price, low_price,
                                    close_price, volume, close_timestamp, trades_number]],
                                    columns=["open_timestamp", "open", "high", "low", "close",
                                            "volume", "close_timestamp", "trades_number",])
            data = pd.concat([data, new_row], axis=0)
    data = data.sort_values(by="open_timestamp", ascending=True, ignore_index=True)
    return data


def generate_vol_per_trade(data: pd.DataFrame) -> pd.DataFrame:
    """generates average volume of quote symbol transferred in a trade

    Args:
        data: Pandas Dataframe object with columns: 
            "open_timestamp", "open", "high", "low", "close", "volume",
            "close_timestamp", "trades_number"

    Returns:
        pd.DataFrame: Pandas Dataframe object with columns: 
            "open_timestamp", "open", "high", "low", "close", "volume",
            "close_timestamp", "trades_number", "volume_per_trade"
    """
    data["volume_per_trade"] = data["volume"] / data["trades_number"]
    return data


def find_base_candles(data: pd.DataFrame, nocffz: int) -> pd.DataFrame:
    """
    Calculates and adds the momentum for every candle in the dataframe,
    then assigns a type (momentum or base) to every candle.

    Args:
        nocffz: number of candles after and candles before every candle 
        that are being used for finding zones \n
        data: Pandas Dataframe object with columns: 
            "open_timestamp", "open", "high", "low", "close", "volume",
            "close_timestamp", "trades_number", "volume_per_trade"

    Returns:
        Pandas Dataframe object with columns: 
            "open_timestamp", "open", "high", "low", "close", "volume",
            "close_timestamp", "trades_number", "volume_per_trade", 
            "candle_type", "momentum"
    """
    data["candle_type"] = "momentum"
    data["momentum"] = [abs(row[1]["close"] - row[1]["open"])
                        for row in data.iterrows()]


    for index in range(nocffz, len(data) - nocffz):
        if (sum([data["momentum"][i] for i in range(index - nocffz, index + nocffz + 1)
                if i != index]) / (2 * nocffz)) > 6 * data["momentum"][index]:
            data.at[index, "candle_type"] = "base"
    
    return data


def find_zones(data: pd.DataFrame, max_num_touches: int) -> pd.DataFrame:
    """Creates a new dataframe containing all valid price action zones

    Args:
        data: Pandas Dataframe object with columns: 
            "open_timestamp", "open", "high", "low", "close", "volume",
            "close_timestamp", "trades_number", "volume_per_trade", 
            "candle_type", "momentum"
        max_num_touches (int): maximum number of candles 
        that touch a zone without making it invalid

    Returns:
        Pandas Dataframe object with columns: 
            "close_timestamp", "high", "low"
    """
    zones = []
    for base_candle_row in data[data["candle_type"] == "base"].iterrows():
        base_candle = base_candle_row[1]
        number_of_touches = 0
        for candle_row in data[data["open_timestamp"] > base_candle["close_timestamp"]].iterrows():
            candle = candle_row[1]
            if (candle["high"] > base_candle["low"] and candle["high"] < base_candle["high"]) or \
            (candle["low"] > base_candle["low"] and candle["low"] < base_candle["high"]):
                number_of_touches += 1
                if number_of_touches > max_num_touches:
                    break
        if number_of_touches <= max_num_touches:
            zones.append({"close_timestamp": base_candle["close_timestamp"],
                        "high": base_candle["high"], "low": base_candle["low"]})

    zones = pd.DataFrame(zones, columns=["close_timestamp", "high", "low"])
    zones = zones.sort_values(by="low", ascending=True, ignore_index=True)
    return zones


def append_zones(zones: pd.DataFrame) -> pd.DataFrame:
    """Appends overlapping zones

    Args:
        zones: Pandas Dataframe object with columns: 
            "close_timestamp", "high", "low"

    Returns:
        Pandas Dataframe object with columns: 
            "close_timestamp", "high", "low"
    """
    appended_zones = pd.DataFrame(columns=["close_timestamp", "high", "low"])
    flag = 0
    for index in range(1, len(zones)):
        if flag == 1:
            flag = 0
            continue
        if zones["high"][index - 1] >= zones["low"][index]:
            new_zone = pd.DataFrame([[zones["close_timestamp"][index - 1], zones["high"]
                                    [index], zones["low"][index - 1]]], columns=["close_timestamp", "high", "low"])
            appended_zones = pd.concat([appended_zones, new_zone], axis=0)
            flag = 1
        else:
            new_zone = pd.DataFrame([[zones["close_timestamp"][index - 1], zones["high"][index - 1],
                                    zones["low"][index - 1]]], columns=["close_timestamp", "high", "low"])
            appended_zones = pd.concat([appended_zones, new_zone], axis=0)
    last_zone = pd.DataFrame([[zones["close_timestamp"][index - 1], zones["high"][len(
        zones) - 1], zones["low"][len(zones) - 1]]], columns=["close_timestamp", "high", "low"])
    appended_zones = pd.concat([appended_zones, last_zone], axis=0)
    appended_zones = appended_zones.reset_index(drop=True)
    return appended_zones


def generate_chart(data: pd.DataFrame, zones: pd.DataFrame) -> None:
    """
    Uses matplotlib to open a chart that shows price and zones

    Args:
        data: Pandas Dataframe object with columns: 
            "open_timestamp", "open", "high", "low", "close", "volume",
            "close_timestamp", "trades_number", "volume_per_trade", 
            "candle_type", "momentum"
        zones: Pandas Dataframe object with columns: 
            "close_timestamp", "high", "low"
    """
    while len(zones) > len(append_zones(zones)):
        zones = append_zones(zones)


    fig, ax = plt.subplots()
    ax.plot(data["close_timestamp"], data["close"])
    ax.set_yscale("log")
    for zone_row in zones.iterrows():
        zone = zone_row[1]
        bottom_left_point_x = zone["close_timestamp"]
        bottom_left_point_y = zone["low"]
        height = zone["high"] - zone["low"]
        width = int(datetime.now().timestamp()*1000) - bottom_left_point_x
        ax.add_patch(Rectangle((bottom_left_point_x, bottom_left_point_y), width,
                    height, edgecolor="red", facecolor="red", fill=True, alpha=0.5))

    plt.show()


data = find_base_candles(generate_vol_per_trade(generate_missing_candles(get_candles("BTCUSDT", int(datetime(2018, 6, 1).timestamp()*1000), "4h"))), 6)
zones = find_zones(data, 4)
generate_chart(data, zones)

