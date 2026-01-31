import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import norm
import matplotlib.pyplot as plt
from dataclasses import dataclass
from scipy.optimize import minimize
pd.set_option('display.float_format', '{:,.4f}'.format)


def get_data(stocks: str | list, start_date: str, end_date: str):
    """
    A function to download stock data from Yahoo Finance.

    Parameters
    -----------
    stocks : str | list
        The stock tickers to download.
    start_date : str
        The start date for the data.
    end_date : str
        The end date for the data.

    Returns:
    -----------
    data : DataFrame

        A DataFrame containing the stock data.
    """

    data=yf.download(stocks, start=start_date, end=end_date)['Close'][stocks]
    return data


def var_stocks(data: pd.DataFrame, n_stocks: list, conf: int | float, long: bool, stocks: list) -> pd.DataFrame:
    """
    Calculate the Value at Risk (VaR) and Conditional Value at Risk (CVaR) for a portfolio of stocks.
    
    Parameters
    -----------
    data : pd.DataFrame
        A DataFrame containing historical stock prices, indexed by date.
    n_stocks : list
        Number of stocks per ticker.
    conf : int | float
        The confidence level for the VaR calculation (e.g., 95 for 95% confidence).
    long : bool
        Indicates the position type:
        - 1 for long positions
        - 0 for short positions
    stocks : list
        A list of column names representing the stocks to be included in the portfolio.
    Returns:
    -----------
    var_stocks_df : pd.DataFrame

        A DataFrame containing the VaR and CVaR values both as percentages and in cash terms.

    Notes: n_stocks and stocks must coincide in lenght and order.
    """

    data = data.sort_index()
    data = data[stocks]
    rt = data.pct_change().dropna()
    stock_value = n_stocks * data.iloc[-1]
    portfolio_value = stock_value.sum()
    w = stock_value / portfolio_value
    portfolio_return = np.dot(w, rt.T)

    var_pct = np.percentile(portfolio_return, 100-conf) if long else np.percentile(portfolio_return, conf)
    cvar_pct = np.abs(portfolio_return[portfolio_return < var_pct].mean()) if long else portfolio_return[portfolio_return > var_pct].mean()

    var_cash, cvar_cash = np.abs(portfolio_value * var_pct), portfolio_value * cvar_pct

    var_stocks_df = pd.DataFrame({
        "Métrica": ["VaR", "cVaR"],
        "Porcentaje": [np.abs(var_pct), cvar_pct],
        "cash": [var_cash, cvar_cash]
    })

    return var_stocks_df


def var_forex(data: pd.DataFrame, positions: list, conf: int | float, long: bool, currencies: list) -> pd.DataFrame:
    """
    Calculate the Value at Risk (VaR) and Conditional Value at Risk (CVaR) for a portfolio of currencies.

    Parameters
    -----------
    data : pd.DataFrame
        A DataFrame containing historical exchange rates, indexed by date.
    positions : list
        A list of positions for each currency.
    conf : int | float
        The confidence level for the VaR calculation (e.g., 95 for 95% confidence).
    long : bool
        Indicates the position type:
        - 1 for long positions
        - 0 for short positions
    currencies : list
        A list of column names representing the currencies to be included in the portfolio.
    
    Returns:
    -----------
    var_df : pd.DataFrame

        A DataFrame containing the VaR and CVaR values both as percentages and in cash terms.
    
    Notes: n_stocks and stocks must coincide in lenght and order.
    """

    data = data.sort_index()
    data = data[currencies]
    port = data * positions
    port['total'] = port.sum(axis=1)
    portfolio_return = port['total'].pct_change().dropna()

    var_porcentual = np.percentile(portfolio_return, 100-conf) if long else np.percentile(portfolio_return, conf)
    cvar_porcentual = np.abs(portfolio_return[portfolio_return < var_porcentual].mean()) if long else portfolio_return[portfolio_return > var_porcentual].mean()

    var_cash, cvar_cash = np.abs(port['total'].iloc[-1] * var_porcentual), port['total'].iloc[-1] * cvar_porcentual

    var_df = pd.DataFrame({
        "Métrica": ["VaR", "cVaR"],
        "Porcentual": [np.abs(var_porcentual), cvar_porcentual],
        "Cash": [var_cash, cvar_cash]
    })

    return var_df


def rebalance_stocks(w_original: list, target_weights: list, data: pd.DataFrame, stocks: list, portfolio_value: float) -> pd.DataFrame:
    """
    Rebalance a portfolio of stocks to achieve target weights.

    Parameters
    -----------
    w_original : list
        The original weights of the portfolio.
    target_weights : list
        The target weights for the portfolio.
    data : pd.DataFrame
        A DataFrame containing historical stock prices, indexed by date.
    stocks : list
        A list of column names representing the stocks to be included in the portfolio.
    portfolio_value : float
        The total value of the portfolio.

    Returns:
    -----------
    w_df : pd.DataFrame

        A DataFrame containing the original and target weights, as well as the number of shares to buy/sell.
    """

    data = data.sort_index()
    data = data[stocks]
    n_stocks = (target_weights - w_original) * portfolio_value / data.iloc[-1]

    w_df = pd.DataFrame({
    "Peso Original": w_original,
    "Peso Óptimo": target_weights,
    "Acciones (C/V)" : n_stocks
    })

    return w_df.T


def var_weights(data: pd.DataFrame, weights: list | np.ndarray, conf: int | float) -> float:
    """
    A function to calculate the Value at Risk (VaR) for a portfolio of stocks.

    Parameters
    -----------
    data : pd.DataFrame
        A DataFrame containing historical stock prices, indexed by date.
    weights : list | np.ndarray
        A list of weights for the portfolio.
    conf : int | float
        The confidence level for the VaR calculation (e.g., 95 for 95% confidence).
    
    Returns:
    -----------
    var : float

        The VaR value for the portfolio.
    """

    data = data.sort_index()
    rt = data.pct_change().dropna()
    portfolio_returns = np.dot(weights, rt.T)
    return np.abs(np.percentile(portfolio_returns, 100-conf))


def cvar_weights(data: pd.DataFrame, weights: list | np.ndarray, conf: int | float) -> float:
    """
    A function to calculate the Conditional Value at Risk (CVaR) for a portfolio of stocks.

    Parameters
    -----------
    data : pd.DataFrame
        A DataFrame containing historical stock prices, indexed by date.
    weights : list | np.ndarray
        A list of weights for the portfolio.
    conf : int | float
        The confidence level for the CVaR calculation (e.g., 95 for 95% confidence).

    Returns:
    -----------
    cvar_pct : float

        The CVaR value for the portfolio.
    """

    data = data.sort_index()
    rt = data.pct_change().dropna()
    portfolio_returns = np.dot(weights, rt.T)
    var = np.percentile(portfolio_returns, 100-conf)
    cvar_pct = np.abs(portfolio_returns[portfolio_returns < var].mean())
    return cvar_pct


def cvar_contributions(weights: list | np.ndarray, returns: pd.DataFrame, alpha: float) -> list:
    """
    A function to calculate the CVaR contributions of each asset in a portfolio.

    Parameters
    -----------
    weights : list | np.ndarray
        A list of weights for the portfolio.
    returns : pd.DataFrame
        A DataFrame containing the returns of the assets in the portfolio.
    alpha : float
        The alpha value for the CVaR calculation (e.g., 0.05 for 95% confidence).

    Returns:
    -----------
    contributions : list

        A list containing the CVaR contributions of each asset in the portfolio.
    """

    n_assets = len(weights)
    # CVaR for only long positions
    def portfolio_return(returns, weights):
        return np.dot(returns, weights)

    def individual_cvar_contributions(weights, returns, alpha):
        portfolio_returns = portfolio_return(returns, weights)
        var = np.percentile(portfolio_returns, alpha*100)

        # check which days are in the cvar for the portfolio
        bad_days_portfolio = portfolio_returns < var

        contributions = []
        # chech the returns of each asset the days where the portfolio is in the cvar to know the contribution
        for i in range(n_assets):
            asset_contribution = -returns.iloc[:, i][bad_days_portfolio].mean() * weights[i]
            contributions.append(asset_contribution)
                
        return contributions
    contributions = individual_cvar_contributions(weights, returns, alpha)
    
    return contributions


def plot_weights(stocks: list, weights: list | np.ndarray):
    """
    A function to plot the weights of a portfolio.

    Parameters
    -----------
    stocks : list
        A list of stock tickers.
    weights : list | np.ndarray
        A list of weights for the portfolio

    Returns:
    -----------
        A pie chart showing the portfolio weights.
    """

    df = pd.DataFrame(weights, index=stocks, columns=['w'])
    filtered_df = df[df['w'] > 0.000001]
    labels = filtered_df.index
    values = filtered_df.iloc[: , 0]

    plt.rcParams['figure.facecolor'] = 'lightgray'
    cmap = plt.get_cmap("Blues")
    custom_colors = cmap(np.linspace(0, 1, len(labels)))
    
    plt.figure(figsize=(8, 8))
    plt.pie(values, labels=labels, autopct='%1.2f%%', startangle=90, colors=custom_colors)
    plt.title("Portfolio Weights")
    plt.show()


def var_apl(data: pd.DataFrame, posiciones: list | np.ndarray, conf: float, long: bool):
    """ 
    A function that calculates the Value at Risk (VaR) and Conditional Value at Risk (CVaR) adjusted by liquidity cost for a portfolio.

    Parameters
    -----------
    data : pd.DataFrame
        A DataFrame containing historical exchange rates, indexed by date.
    posiciones : list | np.ndarray
        A list of positions for each currency.
    conf : float
        The confidence level for the VaR calculation (e.g., 95 for 95% confidence).
    long : bool
        Indicates the position type:
        - 1 for long positions
        - 0 for short positions

    Returns:
    -----------
    resultados : pd.DataFrame

        A DataFrame containing the VaR and CVaR values both as percentages and in cash terms.
    """

    data = data.sort_index()

    # Bid y Ask
    bid_columns = [col for col in data.columns if 'Bid' in col] # Selecciona las columnas que contienen 'Bid'
    ask_columns = [col for col in data.columns if 'Ask' in col] # Selecciona las columnas que contienen 'Ask'

    # Mid
    mid_columns = [f'Mid.{i}' for i in range(len(bid_columns))] # Se crea una lista con los nombres de las columnas de Mid
    data[mid_columns] = (data[bid_columns].values + data[ask_columns].values) / 2

    # Spreads
    spread_columns = [f'Spread.{i}' for i in range(len(bid_columns))] # Se crea una lista con los nombres de las columnas de Spread
    data[spread_columns] = (data[ask_columns].values - data[bid_columns].values) / data[mid_columns].values

    # Returns
    return_columns = [f'Return.{i}' for i in range(len(mid_columns))] # Se crea una lista con los nombres de las columnas de Return
    data[return_columns] = data[mid_columns].pct_change()

    # Weights
    value = posiciones * data[mid_columns].iloc[-1].values
    pv = np.sum(value)
    w = value / pv

    # Portfolio return
    data['port_ret'] = np.dot(data[return_columns], w)

    # VaR calculation
    var_pct = np.percentile(data['port_ret'].dropna(), 100 - conf*100) if long else np.percentile(data['port_ret'].dropna(), conf*100)
    var_cash = pv * var_pct

    # C-VaR calculation
    cvar_pct = data['port_ret'][data['port_ret'] < var_pct].dropna().mean() if long else data['port_ret'][data['port_ret'] > var_pct].dropna().mean()
    cvar_cash = pv * cvar_pct

    # Liquidity cost
    cl_prom = data[spread_columns].mean()
    cl_estr = np.percentile(data[spread_columns], 99, axis=0)

    # VaR adjusted by liquidity cost

    var_apl_prom, var_apl_estr = np.abs(((var_pct - np.dot(w, cl_prom), var_pct - np.dot(w, cl_estr)) if long 
                                else (var_pct + np.dot(w, cl_prom), var_pct + np.dot(w, cl_estr))))

    var_apl_prom_cash, var_apl_estr_cash = np.abs(((var_cash - np.dot(value, cl_prom), var_cash - np.dot(value, cl_estr)) if long 
                                            else (var_cash + np.dot(value, cl_prom), var_cash + np.dot(value, cl_estr))))
    
    # C-VaR adjusted by liquidity cost

    cvar_apl_prom, cvar_apl_estr = np.abs(((cvar_pct - np.dot(w, cl_prom), cvar_pct - np.dot(w, cl_estr)) if long
                                    else (cvar_pct + np.dot(w, cl_prom), cvar_pct + np.dot(w, cl_estr))))
    
    cvar_apl_prom_cash, cvar_apl_estr_cash = np.abs(((cvar_cash - np.dot(value, cl_prom), cvar_cash - np.dot(value, cl_estr)) if long
                                            else (cvar_cash + np.dot(value, cl_prom), cvar_cash + np.dot(value, cl_estr))))

    resultados = pd.DataFrame({
        'Métrica': ['VaR', 'VaR Ajustado Promedio', 'VaR Ajustado Estresado', 'C-VaR', 'C-VaR Ajustado Promedio', 'C-VaR Ajustado Estresado'],
        'Porcentaje': [np.abs(var_pct), var_apl_prom, var_apl_estr, np.abs(cvar_pct), cvar_apl_prom, cvar_apl_estr],
        'Cash': [np.abs(var_cash), var_apl_prom_cash, var_apl_estr_cash, np.abs(cvar_cash), cvar_apl_prom_cash, cvar_apl_estr_cash]
    })

    return resultados


class BlackScholes:
    def __init__(self):
        """
        A class to implement the Black-Scholes model for option pricing and delta hedging.
        
        Methods:
        --------
        - call_delta(S, k, r, sigma, T): Computes the delta of a European call option.
        - put_delta(S, k, r, sigma, T): Computes the delta of a European put option.
        - delta_hedge(info_call, info_put): Computes the total delta of a portfolio of call and put options.
        """

    def _calculate_d1(self, S, k, r, sigma, T):
        """
        Compute the d1 term used in the Black-Scholes model.
        
        Parameters
        -----------
        S : float
            Current stock price.
        k : float
            Strike price of the option.
        r : float
            Risk-free interest rate.
        sigma : float
            Volatility of the stock.
        T : float
            Time to maturity (in years).
        
        Returns:
        --------
        float

            The d1 value used in the Black-Scholes formula.
        """
        return (np.log(S / k) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))

    # Deltas
    def call_delta(self, S, k, r, sigma, T):
        """
        Compute the delta of a European call option.
        
        Parameters
        -----------
        S : float
            Current stock price.
        k : float
            Strike price of the option.
        r : float
            Risk-free interest rate.
        sigma : float
            Volatility of the stock.
        T : float
            Time to maturity (in years).
        
        Returns:
        --------
        float

            Delta of the call option.
        """
        return norm.cdf(self._calculate_d1(S, k, r, sigma, T))

    def put_delta(self, S, k, r, sigma, T):
        """
        Compute the delta of a European put option.
        
        Parameters
        -----------
        S : float
            Current stock price.
        k : float
            Strike price of the option.
        r : float
            Risk-free interest rate.
        sigma : float
            Volatility of the stock.
        T : float
            Time to maturity (in years).
        
        Returns:
        --------
        float

            Delta of the put option.
        """
        return np.abs(norm.cdf(self._calculate_d1(S, k, r, sigma, T)) - 1)

    # Hedge
    def delta_hedge(self, info_call, info_put):
        """
        Compute the total delta of a portfolio containing multiple call and put options.
        
        Parameters
        -----------
        info_call : list of lists
            Each inner list contains the parameters [S, K, r, sigma, T, N] for a call option:
            - S: Current stock price
            - K: Strike price
            - r: Risk-free interest rate
            - sigma: Volatility
            - T: Time to maturity
            - N: Number of contracts
        
        info_put : list of lists
            Each inner list contains the parameters [S, K, r, sigma, T, N] for a put option:
            - S: Current stock price
            - K: Strike price
            - r: Risk-free interest rate
            - sigma: Volatility
            - T: Time to maturity
            - N: Number of contracts
        
        Returns:
        --------
        float

            The total delta of the portfolio.
        """

        # Dataframe for call and put options
        df_call = pd.DataFrame(info_call, columns=['S', 'K', 'r', 'sigma', 'T', 'N'])
        df_put = pd.DataFrame(info_put, columns=['S', 'K', 'r', 'sigma', 'T', 'N'])

        df_call['delta'] = df_call.apply(lambda row: BlackScholes().call_delta(*row[0:-1]), axis=1)
        df_put['delta'] = df_put.apply(lambda row: BlackScholes().put_delta(*row[0:-1]), axis=1)
            
        return np.dot(df_call['N'], df_call['delta']) - np.dot(df_put['N'], df_put['delta'])


class OptimizePortfolioWeights:
    """
    A class to optimize portfolio weights using various methods. The optimization strategies include:
        - Minimum Variance
        - Maximum Sharpe Ratio
        - Minimum Target Semivariance
        - Maximum Omega
        - Minimum CVaR
        - Minimum CVaR Contribution (MCC)
    """

    def __init__(self, returns: pd.DataFrame, risk_free: float):

        self.rets = returns
        self.cov = returns.cov()
        self.rf = risk_free / 252
        self.n_stocks = len(returns.columns)

    # Min Variance
    def opt_min_var(self):

        def var(w): return w.T @ self.cov @ w

        w0 = np.ones(self.n_stocks)/self.n_stocks

        bounds = [(0.05, 1)] * self.n_stocks

        def constraint(w): return sum(w)-1

        result = minimize(fun=var, x0=w0, bounds=bounds,
                          constraints={'fun': constraint, 'type': 'eq'},
                          tol=1e-16)

        return result.x

    # Sharpe Ratio
    def opt_max_sharpe(self):
        rets = self.rets
        rend, cov, rf = self.rets.mean(), self.cov, self.rf

        def sr(w): return -((np.dot(rend, w) - rf) /
                            ((w.reshape(-1, 1).T @ cov @ w) ** 0.5))

        result = minimize(sr, np.ones(len(rets.T)), bounds=[(0.05, None)] * len(rets.T),
                          constraints={'fun': lambda w: sum(
                              w) - 1, 'type': 'eq'},
                          tol=1e-16)

        return result.x

    # Semivariance method
    def opt_min_semivar(self, rets_benchmark):

        rets, corr = self.rets.copy(), self.rets.corr()

        diffs = rets-rets_benchmark.values

        below_zero_target = diffs[diffs < 0].fillna(0)
        target_downside = np.array(below_zero_target.std())

        target_semivariance = np.multiply(target_downside.reshape(
            len(target_downside), 1), target_downside) * corr

        def semivar(w): return w.T @ target_semivariance @ w

        w0 = np.ones(self.n_stocks)/self.n_stocks

        bounds = [(0.05, 3)] * self.n_stocks

        def constraint(w): return sum(w)-1

        result = minimize(fun=semivar, x0=w0, bounds=bounds,
                          constraints={'fun': constraint, 'type': 'eq'}, tol=1e-16)

        return result.x

    # Omega
    def opt_max_omega(self, rets_benchmark):

        rets = self.rets.copy()

        diffs = rets-rets_benchmark.values

        below_zero_target = diffs[diffs < 0].fillna(0)
        above_zero_target = diffs[diffs > 0].fillna(0)

        target_downside = np.array(below_zero_target.std())
        target_upside = np.array(above_zero_target.std())
        o = target_upside/target_downside

        def omega(w): return -sum(o * w)

        w0 = np.ones(self.n_stocks)/self.n_stocks

        bounds = [(0.05, 3)] * self.n_stocks

        def constraint(w): return sum(w)-1

        result = minimize(fun=omega, x0=w0, bounds=bounds,
                          constraints={'fun': constraint, 'type': 'eq'}, tol=1e-16)

        return result.x
    
    # Min CVaR
    def opt_min_cvar(self, alpha):

        returns = self.rets.values

        def portfolio_returns(w):
            return returns @ w

        def cvar_objective(w):
            pr = portfolio_returns(w)

            # Low percentile of returns (left tail)
            var = np.percentile(pr, (1 - alpha) * 100)

            # CVaR as mean of worst returns
            return -pr[pr <= var].mean()

        w0 = np.ones(self.n_stocks) / self.n_stocks
        bounds = [(0.05, 1)] * self.n_stocks
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]

        result = minimize(
            fun=cvar_objective,
            x0=w0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            tol=1e-8
        )

        return result.x
    
    # MCC Portfolio
    def opt_mcc(self, alpha):

        returns = self.rets
        n_assets = self.n_stocks

        def portfolio_returns(w):
            return returns.values @ w

        def individual_cvar_contributions(w):
            pr = portfolio_returns(w)

            # Low percentile of returns (left tail)
            var = np.percentile(pr, (1 - alpha) * 100)

            bad_days = pr <= var

            # Individual CVaR contributions
            contributions = [
                -returns.iloc[bad_days, i].mean() * w[i]
                for i in range(n_assets)
            ]

            return contributions

        def objective(w):
            return np.max(individual_cvar_contributions(w))

        w0 = np.ones(n_assets) / n_assets
        bounds = [(0, 1)] * n_assets
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]

        result = minimize(
            fun=objective,
            x0=w0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            tol=1e-8
        )

        return result.x
    

class DynamicBacktesting(OptimizePortfolioWeights):
    """
    A class to perform dynamic backtesting of portfolio optimization strategies over a specified time horizon.

    Args:
        OptimizePortfolioWeights (Class): A class that provides various portfolio optimization methods.

    Returns:
        A class that performs dynamic backtesting of portfolio optimization strategies.
    """
    
    # Definir las variables que necesitamos dentro de todas las funciones
    def __init__(self, prices, prices_benchmark, capital, rf, months, alpha=0.99):
        self.prices = prices # Atributo para los precios que se almacena en self 
        self.prices_benchmark = prices_benchmark # Atributo para los precios del benchmark que se almacena en self 
        self.months = months # Atributo para los meses que se almacena en self 
        self.capital = capital # Atributos para el capital que se almacena en self 
        self.rf = rf  # Atributa de tasa libre riesgo que se almacena en self 
        self.alpha = alpha # Atributo alpha para CVaR que se almacena en self

        # Inicialización dummy del optimizador (se sobreescribe dinámicamente)
        super().__init__(returns=pd.DataFrame(), risk_free=rf)
        
    # Clase para optimizar los pesos
    def optimize_weights(self, prices: pd.DataFrame, n_days: int, periods: int):
        
        # Extrae el subconjunto de precios actual para el periodo de optimización
        temp_data = prices.iloc[int(n_days * periods):int(n_days * (periods + 1)), :]   
        
        #Extrae el subconjunto de precios del benchmark para el periodo de optimización
        temp_bench = self.prices_benchmark.copy().iloc[int(n_days * periods):int(n_days * (periods + 1)), :]    
        
        # Calcula los rendimientientos del periodo de optimización
        temp_rets = temp_data.pct_change().dropna()  

        rets_benchmark = temp_bench.pct_change().dropna() # Calcula los rendimientos del benchmark para el periodo de optimización

        # --- ACTUALIZACIÓN DEL ESTADO DEL OPTIMIZADOR (HERENCIA) --- #
        self.rets = temp_rets
        self.cov = temp_rets.cov()
        self.n_stocks = temp_rets.shape[1]

        w_minvar = self.opt_min_var()
        w_sharpe = self.opt_max_sharpe()
        w_semivar = self.opt_min_semivar(rets_benchmark)
        w_omega = self.opt_max_omega(rets_benchmark)
        w_min_cvar = self.opt_min_cvar(self.alpha)
        w_mcc = self.opt_mcc(self.alpha)

        # Se devuelven los pesos de los metodos de optimización
        return w_minvar, w_sharpe, w_semivar, w_omega, w_min_cvar, w_mcc

    def simulation(self):
        
        # Son los días redondeados a 0 decimales , son los numero de dias del periodo de la simulación/bt
        n_days = round(len(self.prices) / round(len(self.prices) / 252 / (self.months / 12)), 0) 
        
        # Es el capital inicial de la simulación/bt
        capital = self.capital  

        # Se hace una copia de los precios y se extrae el subconjunto de los precios para el period de optimización
        opt_data = self.prices.copy().iloc[:int(n_days), :]    
        
        # Se hace una copia de los precios y se extrae el subconjunto de los precios para el periodo de simulación/bt
        backtesting_data = self.prices.copy().iloc[int(n_days):, :] 
        
        # Se calculan los rendimientos del periodo de simulación/bt
        backtesting_rets = backtesting_data.pct_change().dropna() 
        
        # Se hace una copia de los precios de benchmark y se extrae el subconjunto de los precios para el periodo y se calculan los rendimientos 
        backtesting_bench = self.prices_benchmark.copy().iloc[int(n_days):, :].pct_change().dropna() 
        
        # Se inicializa los contadores de los días y de los periodos 
        day_counter, periods_counter = 0, 0 
        
        # Lista para almacenar el capital a lo largo del tiempo para estrategia 
        minvar, sharpe, semivar, omega, min_cvar, mcc = [capital], [capital], [capital], [capital], [capital], [capital]
        
        # Se obtienne los pesos optimizados
        w_minvar, w_sharpe, w_semivar, w_omega, w_min_cvar, w_mcc = self.optimize_weights(opt_data, n_days, 0) 
        
        # Se itera dia a dia para 
        for day in range(len(backtesting_data) - 1): 
            
            # Si el contador de dias es menor al numero de didas de optmización , hace: 
            if day_counter < n_days: 

                sharpe.append(sharpe[-1] * (1 + sum(backtesting_rets.iloc[day, :] * w_sharpe)))  
                minvar.append(minvar[-1] * (1 + sum(backtesting_rets.iloc[day, :] * w_minvar)))
                semivar.append(semivar[-1] * (1 + sum(backtesting_rets.iloc[day, :] * w_semivar)))
                omega.append(omega[-1] * (1 + sum(backtesting_rets.iloc[day, :] * w_omega)))
                min_cvar.append(min_cvar[-1] * (1 + sum(backtesting_rets.iloc[day, :] * w_min_cvar)))
                mcc.append(mcc[-1] * (1 + sum(backtesting_rets.iloc[day, :] * w_mcc)))
            else:
                
                w_minvar, w_sharpe, w_semivar, w_omega, w_min_cvar, w_mcc = self.optimize_weights(backtesting_data, n_days, periods_counter)
                    
                sharpe.append(sharpe[-1] * (1 + sum(backtesting_rets.iloc[day, :] * w_sharpe)))
                minvar.append(minvar[-1] * (1 + sum(backtesting_rets.iloc[day, :] * w_minvar)))
                semivar.append(semivar[-1] * (1 + sum(backtesting_rets.iloc[day, :] * w_semivar)))
                omega.append(omega[-1] * (1 + sum(backtesting_rets.iloc[day, :] * w_omega)))
                min_cvar.append(min_cvar[-1] * (1 + sum(backtesting_rets.iloc[day, :] * w_min_cvar)))
                mcc.append(mcc[-1] * (1 + sum(backtesting_rets.iloc[day, :] * w_mcc)))
                periods_counter += 1
                day_counter = 0

            day_counter += 1
        
        # Crear DataFrame con los resultados de la simulación/bt
        df = pd.DataFrame()
        df['Date'] = backtesting_data.index
        df['Date'] = pd.to_datetime(df['Date'])
        df['Min Variance'] = minvar
        df['Sharpe'] = sharpe
        df['Semivariance'] = semivar
        df['Omega'] = omega
        df['Min CVaR'] = min_cvar
        df['MCC'] = mcc
        df.set_index('Date', inplace=True)

        return df
    