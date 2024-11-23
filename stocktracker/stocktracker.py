import datetime
import time
from pathlib import Path
import pyautogui
from selenium import webdriver
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import pandas as pd
import mplcursors
import numpy as np

from multiprocessing.dummy import Pool as ThreadPool


def find_pharma_companies_names(size_company="small", number=5):
    options = webdriver.FirefoxOptions()
    browser = webdriver.Firefox(options=options)
    browser.maximize_window()
    browser.get("https://www.nasdaq.com/market-activity/stocks/screener")
    pyautogui.leftClick(x=1412, y=649, duration=0.5)
    if size_company == "mega" or size_company == "1":
        browser.find_element_by_css_selector("div.symbol-screener__filter-group:nth-child(1) > ul:nth-child(2) > "
                                             "li:nth-child(1) > button:nth-child(1)").click()
    elif size_company == "large" or size_company == "2":
        browser.find_element_by_css_selector("div.symbol-screener__filter-group:nth-child(1) > ul:nth-child(2) > "
                                             "li:nth-child(2) > button:nth-child(1)").click()
    elif size_company == "medium" or size_company == "3":
        browser.find_element_by_css_selector("div.symbol-screener__filter-group:nth-child(1) > ul:nth-child(2) > "
                                             "li:nth-child(3) > button:nth-child(1)").click()
    elif size_company == "small" or size_company == "4":
        browser.find_element_by_css_selector("div.symbol-screener__filter-group:nth-child(1) > ul:nth-child(2) > "
                                             "li:nth-child(4) > button:nth-child(1)").click()
    elif size_company == "micro" or size_company == "5":
        browser.find_element_by_css_selector("div.symbol-screener__filter-group:nth-child(1) > ul:nth-child(2) > "
                                             "li:nth-child(5) > button:nth-child(1)").click()

    pyautogui.scroll(-25)

    browser.find_element_by_css_selector("div.symbol-screener__filter-group:nth-child(3) > ul:nth-child(2) > "
                                         "li:nth-child(2) > button:nth-child(1)").click()
    browser.find_element_by_css_selector(".symbol-screener__apply-button").click()

    pyautogui.scroll(-50)
    time.sleep(5)

    soup = BeautifulSoup(browser.page_source, "html.parser")

    classes = soup.find("ul", {"class": "symbol-screener__pagination"})
    soup = BeautifulSoup(str(classes), "html.parser")
    page_buttons = soup.find_all("a", {"role": "button"})
    dict_names = {}
    pages = len(page_buttons)

    l_page = number // 20
    if l_page < 1:
        l_page = 1
    for page in range(l_page):
        if page > 0 and pages > 3:
            next_btn = browser.find_element_by_class_name("next")
            try:
                next_btn.click()
                time.sleep(3)
            except:
                time.sleep(3)
                next_btn.click()

        soup = BeautifulSoup(browser.page_source, "html.parser")
        comp_names = soup.find_all("tr", {"class": "symbol-screener__row"})

        for names in comp_names:
            if names != "" and len(dict_names) < number:
                splitted = str(names).split(">")
                symbol_name = splitted[3].replace("</a", "")
                full_name = splitted[6].replace("</td", "").replace("amp;", "")
                dict_names[symbol_name] = full_name

    time.sleep(5)
    browser.quit()
    return dict_names


def find_stock_link(stock_name, time_period="5 years", time_interval="1wk"):
    period2 = int(time.time())
    lst_stock_links = []
    if not isinstance(stock_name, list):
        stock_name = [stock_name]
    for stock in stock_name:
        if "year" in time_period:
            period1 = datetime.datetime.utcnow() - datetime.timedelta(days=365 * int(time_period[0:2]) + 1)
            period1 = int(period2 - (datetime.datetime.utcnow() - period1).total_seconds())
            lst_stock_links.append("https://finance.yahoo.com/quote/{}/history?period1={}&period2={}&interval={}&filter"
                                   "=history&frequency={}".format(stock, period1, period2, time_interval,
                                                                  time_interval))
    return lst_stock_links


def gather_stock_data(link):
    # options = webdriver.FirefoxOptions()
    from selenium.webdriver.firefox.service import Service
    from webdriver_manager.firefox import GeckoDriverManager

    options = webdriver.FirefoxOptions()
    service = Service(GeckoDriverManager().install())
    browser = webdriver.Firefox(service=service, options=options)

    stock_name = link.split("/")[4]
    options.add_argument('--ignore-certificate-errors'), options.add_argument('--incognito'), options.add_argument(
        "--headless")
    # browser = webdriver.Firefox(options=options)
    browser.get(link)
    source = browser.page_source
    split_dates = source.split("{\"date\"")[1:]
    index = 0
    for vals in split_dates:
        try:
            if int(vals[2]) and "]" in vals:
                split_dates[index] = split_dates[index].split("]")[0]
        except:
            split_dates.pop(index)
        index += 1
    print("\nGathering data for {} stock".format(stock_name))
    Path("data/{}/".format(stock_name)).mkdir(parents=True, exist_ok=True)
    with open("data/{}/{}.txt".format(stock_name, stock_name), "w") as files:
        files.write("Date,High,Low\n")
        for values in split_dates:
            if "denominator" not in values:
                try:
                    date = time.gmtime(int(values.split(",")[0][1:]))
                    date = str(datetime.datetime(date.tm_year, date.tm_mon, date.tm_mday)).replace(" 00:00:00", "")
                    high, low = round(float(values.split(",")[2].replace("\"high\":", "")), 5), \
                                round(float(values.split(",")[3].replace("\"low\":", "")), 5)
                    files.write("{0},{1},{2}\n".format(date, high, low))
                except ValueError:
                    pass
    print("Done\n")

    browser.quit()
    return "data/{}/{}.txt".format(stock_name, stock_name)


def plot_data_graphs(filename, plot_now=False):
    stock_name = filename.split("/")[1]
    df = pd.read_csv(filename)
    date = df["Date"][::-1]
    fig, ax = plt.subplots(figsize=(18, 9))
    for name in ["High", "Low"]:
        ax.plot(date, df[name][::-1], label=name, linewidth=2)
    ax.set(xlabel="Date", ylabel="Price", title="Stock Prices for {}".format(stock_name))

    mplcursors.cursor()

    plt.gca().margins(x=0)

    max_price = max(df["High"])

    if 1200 < max_price < 2400:
        plt.yticks(np.arange(0, max_price + 50, 50))
    elif max_price < 1200:
        plt.yticks(np.arange(0, max_price + 25, 25))
    elif max_price < 480:
        plt.yticks(np.arange(0, max_price + 10, 10))

    if len(date) / 65 <= 1:
        plt.xticks(np.arange(0, len(date), 1), rotation=90)
    elif len(date) / 65 <= 2.4:
        plt.xticks(np.arange(0, len(date), 2), rotation=90)
    else:
        plt.xticks(np.arange(0, len(date), 4), rotation=90)

    plt.tight_layout()
    plt.legend()
    plt.savefig("data/{}/graph-{}".format(stock_name, stock_name), dpi=250)
    if plot_now:
        plt.show()


if __name__ == '__main__':
    start = time.time()

    option = input("Welcome to StockTracker. I can find and track new stocks for you (healthcare only for now) or"
                   " I could also track data and plot graphs based on a specific stock you're interested in.\n"
                   "Choose 1. If you want to find and track new healthcare stocks.\n"
                   "Choose 2. If you want to track a specific stock.\n")

    try:
        if int(option) == 1:
            size = input("Please select the size of companies you want to look for from the options below.\n"
                         "1. Mega\n2. Large\n3. Medium\n4. Small\n5. Micro\n")

            number = input("Great. Now how many healthcare companies would you like to gather data for? Default is 5.\n"
                           "*Keep in mind: the more companies we need to gather data for,"
                           " the longer the process will take :)\n")

            names_of_companies = find_pharma_companies_names(size.lower(), int(number))
            companies_data_links = find_stock_link(list(names_of_companies.keys()))
            filename = [gather_stock_data(link) for link in companies_data_links]

            for names in filename:
                plot_data_graphs(names)

        else:
            stock_symbol = input("What is the symbol for the stock you want? Ex: Netflix symbol is NFLX.\n")
            stock_link = find_stock_link(stock_symbol)[0]
            file_name = gather_stock_data(stock_link)
            plot_data_graphs(file_name, True)

        duration = time.time() - start
        print("StockTracker gathered all your stocks data in only {} seconds, saved the data and the graphs to"
              " this folder ;)\nThank you for using me. Hope to see you again :)\n".format(round(duration, 4)))

    except ValueError:
        print("Your input is of the wrong type, if I asked for a number, please do not give me words. Try again.\n")
    except:
        print("An unexpected error occured. Ensure you have a strong internet connection and sufficient space on your"
              " computer to download the data and try again.\n")
# import datetime
# import time
# from pathlib import Path
# import pyautogui
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# import matplotlib.pyplot as plt
# from bs4 import BeautifulSoup
# import pandas as pd
# import mplcursors
# import numpy as np


# def find_pharma_companies_names(size_company="small", number=5):
#     """
#     Finds pharmaceutical company names from NASDAQ based on the company size.
#     """
#     try:
#         options = webdriver.FirefoxOptions()
#         browser = webdriver.Firefox(options=options)
#         browser.maximize_window()
#         browser.get("https://www.nasdaq.com/market-activity/stocks/screener")
#         time.sleep(3)  # Ensure page is loaded

#         pyautogui.leftClick(x=1412, y=649, duration=0.5)

#         size_mapping = {
#             "mega": 1,
#             "large": 2,
#             "medium": 3,
#             "small": 4,
#             "micro": 5,
#         }

#         if size_company in size_mapping:
#             browser.find_element(
#                 By.CSS_SELECTOR,
#                 f"div.symbol-screener__filter-group:nth-child(1) > ul:nth-child(2) > "
#                 f"li:nth-child({size_mapping[size_company]}) > button:nth-child(1)"
#             ).click()
#         else:
#             raise ValueError(f"Invalid company size: {size_company}")

#         pyautogui.scroll(-25)

#         browser.find_element(
#             By.CSS_SELECTOR,
#             "div.symbol-screener__filter-group:nth-child(3) > ul:nth-child(2) > li:nth-child(2) > button:nth-child(1)"
#         ).click()
#         browser.find_element(By.CSS_SELECTOR, ".symbol-screener__apply-button").click()

#         pyautogui.scroll(-50)
#         time.sleep(5)

#         soup = BeautifulSoup(browser.page_source, "html.parser")
#         pagination = soup.find("ul", {"class": "symbol-screener__pagination"})
#         page_buttons = pagination.find_all("a", {"role": "button"}) if pagination else []
#         pages = len(page_buttons)

#         dict_names = {}
#         l_page = max(1, number // 20)

#         for page in range(l_page):
#             if page > 0 and pages > 3:
#                 next_btn = browser.find_element(By.CLASS_NAME, "next")
#                 next_btn.click()
#                 time.sleep(3)

#             soup = BeautifulSoup(browser.page_source, "html.parser")
#             comp_names = soup.find_all("tr", {"class": "symbol-screener__row"})

#             for names in comp_names:
#                 if len(dict_names) >= number:
#                     break
#                 splitted = str(names).split(">")
#                 symbol_name = splitted[3].replace("</a", "").strip()
#                 full_name = splitted[6].replace("</td", "").replace("amp;", "").strip()
#                 dict_names[symbol_name] = full_name

#         browser.quit()
#         return dict_names

#     except Exception as e:
#         print(f"Error in find_pharma_companies_names: {e}")
#         return {}


# def find_stock_link(stock_name, time_period="5 years", time_interval="1wk"):
#     """
#     Generates Yahoo Finance URLs for given stock symbols.
#     """
#     try:
#         period2 = int(time.time())
#         lst_stock_links = []
#         if not isinstance(stock_name, list):
#             stock_name = [stock_name]

#         for stock in stock_name:
#             if "year" in time_period:
#                 years = int(time_period.split()[0])
#                 period1 = period2 - (years * 365 * 24 * 60 * 60)
#                 lst_stock_links.append(
#                     f"https://finance.yahoo.com/quote/{stock}/history?period1={period1}&period2={period2}&interval={time_interval}&filter=history&frequency={time_interval}"
#                 )

#         return lst_stock_links

#     except Exception as e:
#         print(f"Error in find_stock_link: {e}")
#         return []


# def gather_stock_data(link):
#     """
#     Fetches stock data from Yahoo Finance for a given link.
#     """
#     try:
#         options = webdriver.FirefoxOptions()
#         stock_name = link.split("/")[4]
#         options.add_argument("--headless")
#         browser = webdriver.Firefox(options=options)
#         browser.get(link)
#         time.sleep(3)

#         source = browser.page_source
#         split_dates = source.split("{\"date\"")[1:]
#         index = 0

#         for vals in split_dates:
#             try:
#                 if int(vals[2]) and "]" in vals:
#                     split_dates[index] = split_dates[index].split("]")[0]
#             except:
#                 split_dates.pop(index)
#             index += 1

#         print(f"\nGathering data for {stock_name} stock")
#         Path(f"data/{stock_name}/").mkdir(parents=True, exist_ok=True)

#         with open(f"data/{stock_name}/{stock_name}.txt", "w") as files:
#             files.write("Date,High,Low\n")
#             for values in split_dates:
#                 try:
#                     date = datetime.datetime.utcfromtimestamp(int(values.split(",")[0][1:])).strftime("%Y-%m-%d")
#                     high = round(float(values.split(",")[2].replace("\"high\":", "")), 5)
#                     low = round(float(values.split(",")[3].replace("\"low\":", "")), 5)
#                     files.write(f"{date},{high},{low}\n")
#                 except ValueError:
#                     pass

#         browser.quit()
#         return f"data/{stock_name}/{stock_name}.txt"

#     except Exception as e:
#         print(f"Error in gather_stock_data: {e}")
#         return ""


# def plot_data_graphs(filename, plot_now=False):
#     """
#     Plots stock data graphs.
#     """
#     try:
#         stock_name = filename.split("/")[1]
#         df = pd.read_csv(filename)
#         date = df["Date"][::-1]

#         fig, ax = plt.subplots(figsize=(18, 9))
#         for name in ["High", "Low"]:
#             ax.plot(date, df[name][::-1], label=name, linewidth=2)

#         ax.set(xlabel="Date", ylabel="Price", title=f"Stock Prices for {stock_name}")
#         mplcursors.cursor()
#         plt.tight_layout()
#         plt.legend()
#         plt.savefig(f"data/{stock_name}/graph-{stock_name}.png", dpi=250)
#         if plot_now:
#             plt.show()

#     except Exception as e:
#         print(f"Error in plot_data_graphs: {e}")


# if __name__ == "__main__":
#     start = time.time()

#     option = input(
#         "Welcome to StockTracker.\n1. Find and track new healthcare stocks.\n2. Track a specific stock.\nChoose: "
#     )

#     try:
#         if option.strip() == "1":
#             size = input("Enter company size (Mega, Large, Medium, Small, Micro): ").lower()
#             number = input("How many companies? Default is 5: ").strip() or "5"

#             names_of_companies = find_pharma_companies_names(size, int(number))
#             companies_data_links = find_stock_link(list(names_of_companies.keys()))
#             filenames = [gather_stock_data(link) for link in companies_data_links]

#             for file in filenames:
#                 plot_data_graphs(file)

#         elif option.strip() == "2":
#             stock_symbol = input("Enter stock symbol (e.g., NFLX): ").upper()
#             stock_link = find_stock_link(stock_symbol)[0]
#             file_name = gather_stock_data(stock_link)
#             plot_data_graphs(file_name, plot_now=True)

#         else:
#             print("Invalid option. Choose either 1 or 2.")

#         duration = time.time() - start
#         print(f"Data gathered in {round(duration, 2)} seconds. Check the saved graphs!")



#     except Exception as e:
#         print(f"Unexpected error: {e}")
