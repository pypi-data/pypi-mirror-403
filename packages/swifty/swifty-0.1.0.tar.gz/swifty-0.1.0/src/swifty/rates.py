import time
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Union
from abc import ABC, abstractmethod



logger = logging.getLogger("SwiftyRates")

class BaseProvider(ABC):
    @abstractmethod
    async def fetch(self, assets: Union[List[str], Dict[str, List[str]]], fiats: List[str]) -> Dict[str, Dict[str, float]]:
        pass

class CoinGeckoProvider(BaseProvider):
    def __init__(self):
        self.asset_to_id = {}
        self.headers = {'User-Agent': 'SwiftyRates/1.0'}
    
    async def _find_id(self, session: aiohttp.ClientSession, symbol: str) -> Optional[str]:
        if symbol.lower() in ['usd', 'usdt']: return 'tether'
        url = f"https://api.coingecko.com/api/v3/search?query={symbol}"
        try:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for coin in data.get('coins', []):
                        if coin['symbol'].lower() == symbol.lower():
                            return coin['id']
        except Exception as e:
            logger.debug(f"CoinGecko search error for {symbol}: {e}")
        return None

    async def fetch(self, assets: List[str], fiats: List[str]):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            for asset in assets:
                if asset not in self.asset_to_id:
                    found_id = await self._find_id(session, asset)
                    if found_id: self.asset_to_id[asset] = found_id

            ids = [self.asset_to_id[a] for a in assets if a in self.asset_to_id]
            if not ids: return {}
            
            vs = ",".join(fiats).lower()
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(ids)}&vs_currencies={vs}"
            
            try:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        id_to_sym = {v: k for k, v in self.asset_to_id.items()}
                        return {id_to_sym[cid]: prices for cid, prices in data.items() if cid in id_to_sym}
            except Exception as e:
                logger.error(f"CoinGecko price fetch error: {e}")
        return {}

class GeckoTerminalProvider(BaseProvider):
    def __init__(self, custom_networks: Dict[str, str] = None):
        self.headers = {'User-Agent': 'SwiftyRates/1.0'}

        synonyms = {
            'ton': ['ton', 'the-open-network'],
            'bsc': ['bsc', 'bnb', 'binance', 'smartchain', 'smart-chain'],
            'polygon_pos': ['pol', 'polygon', 'matic'],
            'solana': ['sol', 'solana'],
            'eth': ['eth', 'ethereum'],
            'tron': ['trx', 'tron'],
            'base': ['base']
        }
        
        self.network_map = {}
        for real_id, aliases in synonyms.items():
            for alias in aliases:
                self.network_map[alias] = real_id

        if custom_networks:
            self.network_map.update({k.lower(): v.lower() for k, v in custom_networks.items()})

    async def _fetch_single(self, session, asset, net_id):
        url = f"https://api.geckoterminal.com/api/v2/search/pools?query={asset}&network={net_id}"
        try:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pools = data.get('data', [])
                    if pools:
                        return asset, float(pools[0]['attributes']['base_token_price_usd'])
        except: pass
        return asset, None

    async def fetch(self, assets: Dict[str, List[str]], fiats: List[str]):
        res = {}
        async with aiohttp.ClientSession(headers=self.headers) as session:
            tasks = []
            for user_net_name, assets in assets.items():
                u_name = user_net_name.lower()
                net_id = self.network_map.get(u_name, u_name)
                
                for asset in assets:
                    tasks.append(self._fetch_single(session, asset, net_id))
            
            results = await asyncio.gather(*tasks)
            for asset, price in results:
                if price and asset.lower() not in res:
                    res[asset.lower()] = {'usd': price}
        return res

class ExchangeProvider(BaseProvider):
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.headers = {'User-Agent': 'SwiftyRates/1.0'}

    async def fetch(self, assets: List[str], fiats: List[str]):
        res = {}
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(self.base_url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        tickers = data if isinstance(data, list) else data.get('result', {}).get('list', [])
                        
                        if not tickers:
                            logger.warning(f"No tickers found in {self.name} response")
                            return res

                        for t in tickers:
                            symbol = t.get('symbol', '').upper()
                            if symbol.endswith('USDT'):
                                asset_name = symbol.replace('USDT', '').lower()
                                if asset_name in assets:
                                    raw_price = t.get('price') or t.get('lastPrice')
                                    if raw_price:
                                        res[asset_name] = {'usd': float(raw_price)}
        except Exception as e:
            logger.error(f"Error fetching from {self.name}: {e}")
        return res

class ForexProvider(BaseProvider):
    def __init__(self):
        self.url = "https://open.er-api.com/v6/latest/USD"
        self._cache = {}
        self._last_update = 0

    async def fetch(self, assets: List[str], fiats: List[str]):
        current_time = time.time()
        if current_time - self._last_update < 3600 and self._cache:
            return self._cache
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        rates = data.get('rates', {})
                        result = {'usd_base': {f.lower(): rates.get(f.upper(), 0.0) for f in fiats}}
                        
                        self._cache = result
                        self._last_update = current_time
                        
                        return result
        except Exception as e:
            logger.error(f"Forex fetch error: {e}")
        return {}


class SwiftyRates:
    def __init__(self, assets: Dict[str, List[str]], fiats: List[str], providers: List[BaseProvider] = None):
        self.assets = {k.lower(): [v.lower() for v in val] for k, val in assets.items()}
        
        self.all_assets = []
        for asset_list in self.assets.values():
            self.all_assets.extend(asset_list)
        self.all_assets = list(set(self.all_assets))

        self.fiats = [f.lower() for f in fiats]
        self.providers = providers or [
            CoinGeckoProvider(),
            GeckoTerminalProvider(),
            ExchangeProvider("Binance", "https://api.binance.com/api/v3/ticker/price"),
            ExchangeProvider("Bybit", "https://api.bybit.com/v5/market/tickers?category=spot"),
            ForexProvider()
        ]
        self.rates = {}
        self._last_run = 0

    async def update(self) -> bool:
        current_time = time.time()
        if current_time - self._last_run < 10:
            logger.warning("Update called too frequently. Skipping to avoid API ban.")
            return False
            
        tasks = []
        for p in self.providers:
            if isinstance(p, GeckoTerminalProvider):
                tasks.append(p.fetch(self.assets, self.fiats))
            else:
                tasks.append(p.fetch(self.all_assets, self.fiats))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)

        self._last_run = current_time

        usd_to_fiat = {f: 0.0 for f in self.fiats}
        usd_to_fiat['usd'] = 1.0

        for data in results:
            if isinstance(data, dict) and 'usd_base' in data:
                usd_to_fiat.update(data['usd_base'])

        crypto_prices = {a: [] for a in self.all_assets}
        for data in results:
            if isinstance(data, Exception) or not data: 
                continue
            for asset, prices in data.items():
                if asset in crypto_prices and 'usd' in prices:
                    val = prices['usd']
                    if val > 0:
                        crypto_prices[asset].append(val)

        new_rates = {'usd_base': usd_to_fiat}
        for asset in self.all_assets:
            prices = crypto_prices.get(asset, [])
            if not prices:
                if asset in self.rates: 
                    new_rates[asset] = self.rates[asset]
                continue

            avg_usd = sum(prices) / len(prices)
            new_rates[asset] = {f: round(avg_usd * usd_to_fiat[f], 8) for f in self.fiats}

        if new_rates:
            self.rates = new_rates
            return True
        return False

    def get_price(self, asset: str, currency: str = "usd") -> float:
        asset = asset.lower()
        currency = currency.lower()

        if asset in ['usd', 'usdt']:
            return self.rates.get('usd_base', {}).get(currency, 1.0 if currency == 'usd' else 0.0)

        return self.rates.get(asset, {}).get(currency, 0.0)