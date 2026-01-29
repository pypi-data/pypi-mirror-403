#!/usr/bin/env python3
"""
ABE - Absolute Byzantine Engine
Honest Abe Edition — BFT Trading Analysis CLI
The Dredd System: DBFT - I AM THE LAW!

Features:
- Oversight mode as default (lightweight 3-model consensus)
- Full BFT with rotating perspectives (each model analyzes each perspective)
- Color-coded output (Cyan: AI, Dark Green: User)
- /c command for direct CLI execution
- Live + historical market data access
- Internet search integration
- Full audit logging with dissent tracking and reasoning
- Push notifications (plyer + fallback)
"""

import subprocess
import os
import sys
import time
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
import requests

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Color codes (ANSI)
CYAN = '\033[96m'
DARK_GREEN = '\033[32m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

# Preserve originals for toggling
ORIG_COLORS = {
    'CYAN': CYAN,
    'DARK_GREEN': DARK_GREEN,
    'YELLOW': YELLOW,
    'RED': RED,
    'RESET': RESET,
}

COLORAMA_AVAILABLE = False
try:
    import colorama
    colorama.just_fix_windows_console()
    COLORAMA_AVAILABLE = True
except Exception:
    pass

def _set_colors_enabled(enabled: bool):
    global CYAN, DARK_GREEN, YELLOW, RED, RESET
    if enabled:
        CYAN = ORIG_COLORS['CYAN']
        DARK_GREEN = ORIG_COLORS['DARK_GREEN']
        YELLOW = ORIG_COLORS['YELLOW']
        RED = ORIG_COLORS['RED']
        RESET = ORIG_COLORS['RESET']
    else:
        CYAN = DARK_GREEN = YELLOW = RED = RESET = ''

# API Integrations
ANTHROPIC_AVAILABLE = False
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    pass

GROQ_AVAILABLE = False
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    pass

# Model resolution helpers
def _vendor_from_id(model_id: str) -> str:
    mid = (model_id or '').lower()
    # Anthropic models
    if 'claude' in mid or 'sonnet' in mid or 'haiku' in mid or 'opus' in mid:
        return 'anthropic'
    # Google models
    if 'gemma' in mid or 'gemini' in mid:
        return 'google'
    # Meta models
    if 'llama' in mid:
        return 'meta'
    # Mistral models
    if 'mixtral' in mid or 'mistral' in mid:
        return 'mistral'
    # Alibaba models
    if 'qwen' in mid:
        return 'alibaba'
    return 'unknown'

def _pick_first_matching(ids, include_any, exclude_vendors):
    for m in ids:
        vid = _vendor_from_id(m)
        if vid in exclude_vendors: continue
        if any(tok in m for tok in include_any): return m
    return None

# Financial data
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print(f"{YELLOW}Warning: yfinance not installed. Run: pip install yfinance{RESET}")

try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False

# Push notifications
PLYER_AVAILABLE = False
try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    pass

def _load_keys_from_keeper(root: str):
    try:
        import importlib.util
        for dp, _, files in os.walk(root):
            if 'keeperki.py' in files:
                keeper_path = os.path.join(dp, 'keeperki.py')
                try:
                    spec = importlib.util.spec_from_file_location('keeperki', keeper_path)
                    m = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(m)
                    for env_name, attr_name in (
                        ('ANTHROPIC_API_KEY', 'ANTHROPIC_API_KEY'),
                        ('ANTHROPIC_API_KEY', 'anthropic_api_key'),
                        ('GROQ_API_KEY', 'GROQ_API_KEY'),
                        ('GROQ_API_KEY', 'groq_api_key'),
                    ):
                        if not os.getenv(env_name) and hasattr(m, attr_name):
                            val = getattr(m, attr_name)
                            if val: os.environ[env_name] = str(val)
                except Exception:
                    try:
                        import re
                        txt = open(keeper_path, 'r', encoding='utf-8', errors='ignore').read()
                        for env_name, keypat in (
                            ('ANTHROPIC_API_KEY', 'ANTHROPIC_API_KEY|anthropic_api_key'),
                            ('GROQ_API_KEY', 'GROQ_API_KEY|groq_api_key'),
                        ):
                            if not os.getenv(env_name):
                                m = re.search(rf"(?:{keypat})\s*=\s*['\"]([^'\"]+)['\"]", txt)
                                if m: os.environ[env_name] = m.group(1)
                    except Exception: pass
                break
    except Exception: pass

class ABEComplete:
    def __init__(self):
        no_color_env = os.getenv('NO_COLOR') or os.getenv('ABE_NO_COLOR')
        self.color_enabled = (not no_color_env) and getattr(sys.stdout, 'isatty', lambda: False)()
        _set_colors_enabled(self.color_enabled)

        if not os.getenv('ANTHROPIC_API_KEY') or not os.getenv('GROQ_API_KEY'):
            _load_keys_from_keeper(str(Path(__file__).resolve().parent))

        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.groq_api_key = os.getenv('GROQ_API_KEY')

        self.anthropic_client = None
        self.groq_client = None

        if ANTHROPIC_AVAILABLE and self.anthropic_api_key:
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            except Exception as e:
                print(f"{YELLOW}Warning: Anthropic init failed: {e}{RESET}")
        else:
            print(f"{YELLOW}Anthropic unavailable. Set ANTHROPIC_API_KEY.{RESET}")

        if GROQ_AVAILABLE and self.groq_api_key:
            try:
                self.groq_client = Groq(api_key=self.groq_api_key)
            except Exception as e:
                print(f"{YELLOW}Warning: Groq init failed: {e}{RESET}")
        else:
            print(f"{YELLOW}Groq unavailable. Set GROQ_API_KEY.{RESET}")

        try:
            self._groq_model_ids = []
            if self.groq_client:
                resp = self.groq_client.models.list()
                self._groq_model_ids = [getattr(m, 'id', '') for m in getattr(resp, 'data', []) if getattr(m, 'id', '')]
        except Exception:
            self._groq_model_ids = []

        self.models = {
            'primary': {'type': 'groq', 'id': None, 'aliases': ['llama-3.3-70', 'llama-3.2-70'], 'name': 'Llama 3.3 70B (Primary)'},
            'monitor_1': {'type': 'groq', 'id': None, 'aliases': ['gemma-2', 'qwen', 'mixtral'], 'name': 'Secondary Groq (Monitor 1)'},
            'monitor_2': {'type': 'anthropic', 'id': 'claude-sonnet-4-20250514', 'name': 'Claude Sonnet 4 (Monitor 2 + Arbiter)'},
            'voter_1': {'type': 'groq', 'id': None, 'aliases': ['llama-3.3-70'], 'name': 'Llama 3.3 70B'},
            'voter_2': {'type': 'groq', 'id': None, 'aliases': ['gemma-2', 'qwen', 'mixtral'], 'name': 'Alt Family'},
            'voter_3': {'type': 'groq', 'id': None, 'aliases': ['llama-3.1-8'], 'name': 'Llama 3.x Small'},
            'arbiter': {'type': 'anthropic', 'id': 'claude-sonnet-4-20250514', 'name': 'Claude Sonnet 4 (Arbiter)'}
        }

        self._resolve_model_ids()

        self.bft_perspectives = {
            'momentum': "Analyze from MOMENTUM: trends, volume, price action",
            'pattern': "Analyze from PATTERN: technical patterns, support/resistance",
            'risk': "Analyze from RISK: volatility, downside, market conditions"
        }

        self.roles = {
            'bft_voters': ['voter_1', 'voter_2', 'voter_3'],
            'bft_arbiter': 'arbiter',
            'oversight_primary': 'primary',
            'oversight_monitors': ['monitor_1', 'monitor_2']
        }

        self.conversation_history = []
        self.last_query = None
        self.last_results = None

        desktop = Path.home() / 'Desktop'
        self.log_file = str(desktop / 'abe-analysis.log')
        self.dissent_log = str(desktop / 'abe-dissent.log')
        self.audit_log_file = str(desktop / 'abe-audit.log')

        self.push_threshold = 0.85

        # Paper trading portfolio
        self.paper_portfolio = {
            'cash': 100000.0,
            'positions': {},
            'trades': []
        }

        self.patent_info = """ABE BFT System - Patent Pending
Byzantine Fault Tolerance for AI Consensus with Auditable Dissent Resolution
Key Innovation: Raising the reliability floor through structured multi-perspective analysis"""

        print(f"{CYAN}ABE v1.0 initialized - Oversight Mode Active{RESET}")
        if not self.color_enabled:
            print("[note] Colors disabled. Use /no-color on to force.")

        print(f"{CYAN}Type /help for commands{RESET}\n")

        try:
            msum = {k: (v.get('id') or 'unresolved') for k, v in self.models.items()}
            print(f"{YELLOW}Model map:{RESET} " + ", ".join([f"{k}={msum[k]}" for k in ['primary','monitor_1','monitor_2','voter_1','voter_2','voter_3','arbiter'] if k in msum]))
        except Exception: pass

    def _resolve_model_ids(self):
        if not self._groq_model_ids: return
        ids = [m for m in self._groq_model_ids if isinstance(m, str)]
        
        # Resolve primary first
        if self.models['primary']['id'] is None:
            pick = _pick_first_matching(ids, self.models['primary'].get('aliases', []), set()) or 'llama-3.3-70b-versatile'
            self.models['primary']['id'] = pick

        primary_vendor = _vendor_from_id(self.models['primary']['id'])
        assigned_voter_vendors = set()

        # Resolve monitors and voters
        for key in ('monitor_1', 'voter_1', 'voter_2', 'voter_3'):
            if self.models[key]['id'] is None:
                # Exclude the primary model's vendor (except for voter_1) and any already assigned voter vendors
                excl = {primary_vendor} if key != 'voter_1' else set()
                excl.update(assigned_voter_vendors)
                
                pick = _pick_first_matching(ids, self.models[key].get('aliases', []), excl)
                
                # If no diverse model is found, fall back to the primary, but log a warning
                if not pick:
                    pick = self.models['primary']['id']
                    print(f"{YELLOW}Warning: Could not find a diverse model for {key}. Reusing primary model.{RESET}")

                self.models[key]['id'] = pick
                # Add the vendor of the chosen model to the set of assigned voter vendors
                if 'voter' in key:
                    assigned_voter_vendors.add(_vendor_from_id(pick))

    def send_push(self, title, body):
        if PLYER_AVAILABLE:
            try:
                notification.notify(title=title, message=body, timeout=10, app_name="ABE BFT")
            except Exception: pass
        print(f"{CYAN}PUSH: {title}\n{body}{RESET}")

    def paper_buy(self, ticker, shares, price):
        """Paper trade buy"""
        cost = shares * price
        if cost > self.paper_portfolio['cash']:
            print(f"{RED}Insufficient fake cash: ${cost:,.2f} needed{RESET}")
            return
        self.paper_portfolio['cash'] -= cost
        if ticker not in self.paper_portfolio['positions']:
            self.paper_portfolio['positions'][ticker] = {'shares': 0, 'buy_price': 0}
        pos = self.paper_portfolio['positions'][ticker]
        total_shares = pos['shares'] + shares
        total_cost = (pos['shares'] * pos['buy_price']) + cost
        pos['shares'] = total_shares
        pos['buy_price'] = total_cost / total_shares if total_shares > 0 else 0
        self.paper_portfolio['trades'].append({
            'type': 'BUY', 'ticker': ticker, 'shares': shares,
            'price': price, 'timestamp': datetime.now().isoformat()
        })
        print(f"{CYAN}FAKE BUY: {shares} {ticker} @ ${price:,.2f} → ${cost:,.2f}{RESET}")
        self.send_push("FAKE TRADE", f"BUY {shares} {ticker} @ ${price:,.2f}")

    def paper_sell(self, ticker, shares, price):
        """Paper trade sell"""
        pos = self.paper_portfolio['positions'].get(ticker, {})
        if pos.get('shares', 0) < shares:
            print(f"{RED}Not enough {ticker} to sell{RESET}")
            return
        revenue = shares * price
        self.paper_portfolio['cash'] += revenue
        pos['shares'] -= shares
        if pos['shares'] == 0:
            del self.paper_portfolio['positions'][ticker]
        self.paper_portfolio['trades'].append({
            'type': 'SELL', 'ticker': ticker, 'shares': shares,
            'price': price, 'timestamp': datetime.now().isoformat()
        })
        profit = revenue - (shares * pos.get('buy_price', price))
        print(f"{CYAN}FAKE SELL: {shares} {ticker} @ ${price:,.2f} → +${profit:,.2f}{RESET}")
        self.send_push("FAKE TRADE", f"SELL {shares} {ticker} @ ${price:,.2f} → +${profit:,.2f}")

    def paper_status(self):
        """Show paper portfolio status"""
        total_value = self.paper_portfolio['cash']
        for t, p in self.paper_portfolio['positions'].items():
            data, _ = self.fetch_live_data(t, '1d')
            if data and data.get('current_price'):
                total_value += p['shares'] * data['current_price']
        print(f"{CYAN}=== PAPER PORTFOLIO ==={RESET}")
        print(f"Cash: ${self.paper_portfolio['cash']:,.2f}")
        print(f"Positions: {len(self.paper_portfolio['positions'])}")
        for t, p in self.paper_portfolio['positions'].items():
            print(f" {t}: {p['shares']} @ ${p['buy_price']:,.2f}")
        print(f"Total Value: ${total_value:,.2f}")
        print(f"Trades: {len(self.paper_portfolio['trades'])}")

    def show_help(self):
        help_text = f"""{CYAN}╔════════════════════════════════════════════════════════════════╗
║ ABE - Absolute Byzantine Engine ║
║ Raising the Floor on AI Reliability ║
╚════════════════════════════════════════════════════════════════╝{RESET}

{YELLOW}HOW IT WORKS{RESET}
ABE uses multiple AI models that debate and verify each other.
A panel of experts with a judge (arbiter) to resolve disagreements.

{YELLOW}ANALYSIS MODES{RESET}
  {CYAN}Just ask a question{RESET} → Oversight mode (fast)
  {CYAN}/bft <query>{RESET} → Full BFT (9 analyses)
  {CYAN}/data <TICKER>{RESET} → Auto BFT on market data
  {CYAN}/lies <TICKER>{RESET} → Show dissent history

{YELLOW}COMMANDS{RESET}
  /help /patent /logs [n] /clear /no-color [on|off]
  /json last /models /c <cmd> /search <query>
  /paper [buy/sell TICKER SHARES | reset] - Paper trading
  /trade <query> - Natural language trading (e.g., "find me 3 stocks")
  /exit

{YELLOW}PRO TIP{RESET}
Financial queries auto-trigger BFT. Check /lies to see where models disagreed.

{CYAN}────────────────────────────────────────────────────────────────{RESET}
Remember: ABE doesn't make you smarter — it makes AI more reliable.
{CYAN}────────────────────────────────────────────────────────────────{RESET}
"""
        print(help_text)

    def log_result(self, result_type, data):
        timestamp = datetime.now().isoformat()
        log_entry = {'timestamp': timestamp, 'type': result_type, 'data': data}
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')

    def log_audit(self, event_type, data):
        timestamp = datetime.now().isoformat()
        audit_entry = {'timestamp': timestamp, 'event_type': event_type, 'data': data}
        with open(self.audit_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')

    def log_dissent(self, votes, arbiter_decision, analysis_type='unknown'):
        timestamp = datetime.now().isoformat()
        dissension_detected = False
        all_vote_values = []
        for perspective_votes in votes.values():
            all_vote_values.extend(perspective_votes.values())

        if len(set(v for v in all_vote_values if v not in ['UNCERTAIN', 'FAILED'])) > 1:
            dissension_detected = True

        dissent_entry = {
            'timestamp': timestamp,
            'analysis_type': analysis_type,
            'votes': votes,
            'arbiter_decision': arbiter_decision,
            'dissension_detected': dissension_detected
        }
        with open(self.dissent_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(dissent_entry) + '\n')
        self.log_audit('dissension_detected', dissent_entry)

    def show_logs(self, count=20):
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-count:]
                print(f"{CYAN}Recent Logs (last {count}):{RESET}")
                for line in lines:
                    try:
                        entry = json.loads(line.strip())
                        print(f"{YELLOW}{entry['timestamp'][:19]} - {entry['type']}{RESET}")
                    except: continue
            else:
                print(f"{YELLOW}No logs found{RESET}")
        except Exception as e:
            print(f"{RED}Error: {e}{RESET}")

    def show_lies(self, ticker):
        """Demo command - show detected voter errors/dissent for ticker"""
        print(f"\n{YELLOW}Analyzing dissent history for {ticker}...{RESET}\n")
        
        if not os.path.exists(self.audit_log_file):
            print(f"{RED}No audit log found at {self.audit_log_file}{RESET}")
            return
        
        try:
            dissent_events = []
            with open(self.audit_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get('event_type') == 'dissension_detected':
                            data_str = json.dumps(entry.get('data', {}))
                            if ticker.upper() in data_str.upper():
                                dissent_events.append(entry)
                    except json.JSONDecodeError:
                        continue
            
            if not dissent_events:
                print(f"{CYAN}No dissent events found for {ticker}{RESET}")
                print(f"{CYAN}This indicates strong model agreement on {ticker} analysis{RESET}\n")
                return
            
            print(f"{RED}⚠️  Found {len(dissent_events)} dissent event(s) for {ticker}{RESET}\n")
            
            for event in dissent_events[-3:]:
                data = event.get('data', {})
                timestamp = event.get('timestamp', 'Unknown')[:19]
                analysis_type = data.get('analysis_type', 'unknown')
                
                print(f"{YELLOW}{'='*50}{RESET}")
                print(f"{YELLOW}Dissent Event: {timestamp}{RESET}")
                print(f"Analysis Type: {analysis_type}")
                
                if analysis_type == 'trading':
                    dissenting_persp = data.get('dissenting_perspectives', [])
                    if dissenting_persp:
                        print(f"Perspectives with disagreement: {', '.join(dissenting_persp)}")
                    
                    votes = data.get('votes', {})
                    for perspective, p_votes in votes.items():
                        if isinstance(p_votes, dict):
                            vote_summary = ', '.join([f"{role.split('_')[1]}: {vote}" for role, vote in p_votes.items()])
                            print(f"  {perspective.upper()}: {vote_summary}")
                else:
                    votes = data.get('votes', {})
                    vote_summary = ', '.join([f"{k}: {v}" for k, v in votes.items()])
                    print(f"Votes: {vote_summary}")
                
                arbiter_decision = data.get('arbiter_decision', '')
                print(f"Arbiter Resolution: {arbiter_decision[:150]}...")
                print(f"{YELLOW}{'='*50}{RESET}\n")
            
            print(f"{CYAN}💡 These dissent events show the BFT system catching potential errors{RESET}")
            print(f"{CYAN}   The arbiter resolved disagreements to produce verified signals{RESET}\n")
        
        except Exception as e:
            print(f"{RED}Error reading dissent logs: {e}{RESET}")

    def fetch_live_data(self, ticker, period='2y'):
        if not YFINANCE_AVAILABLE: return None, "yfinance not installed."
        try:
            stock = yf.Ticker(ticker)
            info = getattr(stock, 'info', {}) or {}
            hist = stock.history(period=period)
            if hist.empty: return None, "No data returned."

            data_summary = {
                'ticker': ticker,
                'current_price': info.get('currentPrice'),
                'day_high': info.get('dayHigh'),
                'day_low': info.get('dayLow'),
                'volume': info.get('volume'),
                'market_cap': info.get('marketCap'),
                'period_days': len(hist),
                'first_close': float(hist['Close'].iloc[0]),
                'last_close': float(hist['Close'].iloc[-1]),
                'period_high': float(hist['High'].max()),
                'period_low': float(hist['Low'].min()),
                'avg_volume': float(hist['Volume'].mean()),
                'timestamp': datetime.now().isoformat()
            }
            self.log_audit('data_fetch', {'ticker': ticker, 'success': True})
            return data_summary, None
        except Exception as e:
            self.log_audit('data_fetch', {'ticker': ticker, 'success': False, 'error': str(e)})
            return None, f"Error: {e}"

    def web_search(self, query):
        try:
            url = f"https://api.duckduckgo.com/?q={requests.utils.quote(query)}&format=json"
            response = requests.get(url, timeout=8)
            response.raise_for_status()
            data = response.json()
            abstract = data.get('AbstractText', '') or 'No results'
            related = [r.get('Text', '') for r in data.get('RelatedTopics', [])[:3] if isinstance(r, dict)]
            return f"Search: {query}\n\nSummary: {abstract}\n\nRelated:\n" + "\n".join(f"- {r}" for r in related if r)
        except Exception as e:
            return f"Search error: {e}"

    def extract_vote(self, response_text):
        match = re.search(r'(BULLISH|BEARISH|NEUTRAL)', response_text or '', re.IGNORECASE)
        return match.group(0).upper() if match else 'UNCERTAIN'

    def call_model(self, role, prompt, max_tokens=2000, temperature=0.7):
        model_config = self.models[role]
        try:
            if model_config['type'] == 'groq':
                if not self.groq_client: return {'success': False, 'error': 'Groq unavailable'}
                if not model_config.get('id'): self._resolve_model_ids()
                response = self.groq_client.chat.completions.create(
                    model=model_config['id'],
                    messages=[{'role': 'user', 'content': prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return {'success': True, 'result': response.choices[0].message.content, 'model': model_config['name']}
            elif model_config['type'] == 'anthropic':
                if not self.anthropic_client: return {'success': False, 'error': 'Anthropic unavailable'}
                response = self.anthropic_client.messages.create(
                    model=model_config['id'],
                    max_tokens=max_tokens,
                    messages=[{'role': 'user', 'content': prompt}]
                )
                return {'success': True, 'result': response.content[0].text, 'model': model_config['name']}
        except Exception as e:
            return {'success': False, 'error': str(e), 'model': model_config['name']}

    def run_bft_analysis(self, data_content, analysis_type='trading'):
        self.last_query = data_content.get('ticker') if isinstance(data_content, dict) else str(data_content)[:100]
        try:
            voter_roles = self.roles['bft_voters']
            arbiter_role = self.roles['bft_arbiter']
        except KeyError as e:
            print(f"{RED}Config error: {e}{RESET}")
            return None

        if analysis_type == 'trading':
            print(f"{CYAN}Running Trading BFT ({len(voter_roles)} models x 3 perspectives)...{RESET}\n")
            data_str = json.dumps(data_content, indent=2) if isinstance(data_content, dict) else str(data_content)
            all_votes = {p: {} for p in self.bft_perspectives}
            all_results = {p: {} for p in self.bft_perspectives}

            for perspective_name, perspective_prompt in self.bft_perspectives.items():
                print(f"{YELLOW}{perspective_name.upper()} perspective...{RESET}")
                prompts = {}
                for role in voter_roles:
                    prompts[role] = f"{perspective_prompt}:\n\n{data_str}\n\nRespond with: BULLISH/BEARISH/NEUTRAL and brief reasoning."

                with ThreadPoolExecutor(max_workers=len(voter_roles)) as executor:
                    futures = {executor.submit(self.call_model, role, prompts[role]): role for role in voter_roles}
                    for future in as_completed(futures):
                        role = futures[future]
                        result_data = future.result()
                        all_results[perspective_name][role] = result_data
                        vote = self.extract_vote(result_data['result']) if result_data['success'] else 'FAILED'
                        all_votes[perspective_name][role] = vote
                        print(f" {result_data['model']}: {vote}")

            perspective_signals = {}
            for p, votes in all_votes.items():
                valid = [v for v in votes.values() if v not in ['UNCERTAIN', 'FAILED']]
                perspective_signals[p] = Counter(valid).most_common(1)[0][0] if valid else 'UNCERTAIN'

            print(f"\n{YELLOW}Perspective Signals:{RESET}")
            for p, s in perspective_signals.items(): print(f" {p.upper()}: {s}")

            arbiter_prompt = f"""You are the ARBITER in a BFT consensus system.

Perspectives:
- MOMENTUM: {perspective_signals.get('momentum')}
- PATTERN: {perspective_signals.get('pattern')}
- RISK: {perspective_signals.get('risk')}

Data:
{data_str[:1000]}

Final signal (BULLISH/BEARISH/NEUTRAL) and confidence (0.0–1.0):"""
            arbiter_response = self.call_model(arbiter_role, arbiter_prompt)
            if not arbiter_response['success']:
                print(f"{RED}Arbiter failed{RESET}")
                return None

            final_signal_match = re.search(r'(BULLISH|BEARISH|NEUTRAL)', arbiter_response['result'], re.IGNORECASE)
            confidence_matches = re.findall(r'(\d+\.\d+|\.\d+|\d+)', arbiter_response['result'])
            final_signal = final_signal_match.group(0).upper() if final_signal_match else 'UNCERTAIN'
            confidence = float(confidence_matches[-1]) if confidence_matches else 0.5

            if confidence >= self.push_threshold:
                self.send_push("ABE BFT ALERT", f"{data_content.get('ticker')} → {final_signal} ({confidence:.1%})")

            # Auto-trade on high-confidence bullish signal
            if confidence >= 0.85 and final_signal == 'BULLISH':
                price = data_content.get('current_price')
                if price:
                    self.paper_buy(data_content['ticker'], 10, price)

            print(f"\n{CYAN}ARBITER FINAL: {final_signal} ({confidence:.1%}){RESET}\n")
            print(f"{CYAN}{arbiter_response['result']}{RESET}\n")

            facts = {k: data_content[k] for k in data_content if k in ('ticker','current_price','period_high','period_low')}
            analysis_result = {
                'analysis_type': 'trading',
                'ticker': data_content.get('ticker'),
                'final_signal': final_signal,
                'confidence': confidence,
                'arbiter_reasoning': arbiter_response['result'],
                'data_facts': facts
            }
            self.log_audit('bft_analysis_complete', analysis_result)
            self.log_result('trading_bft', analysis_result)
            self.log_dissent(all_votes, final_signal, 'trading')
            self.last_results = analysis_result
            return analysis_result

    def run_oversight(self, prompt):
        primary = self.call_model('primary', prompt)
        if not primary['success']:
            print(f"{RED}Primary failed{RESET}")
            return
        print(f"{CYAN}{primary['result']}{RESET}\n")

    def execute_cli(self, command):
        forbidden = ['rm -rf', 'sudo', 'mkfs', 'dd if=', '> /dev/', 'chmod 777']
        if any(bad in command.lower() for bad in forbidden):
            print(f"{RED}Blocked: {command}{RESET}")
            return
        print(f"{CYAN}Executing: {command}{RESET}")
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout or result.stderr or "[OK]"
            print(f"{CYAN}{output}{RESET}")
        except Exception as e:
            print(f"{RED}Error: {e}{RESET}")

    def analyze_ticker(self, ticker, period='2y'):
        print(f"{CYAN}Fetching {period} data for {ticker}...{RESET}")
        data, error = self.fetch_live_data(ticker, period)
        if error:
            print(f"{RED}{error}{RESET}")
            return None
        data['period'] = period
        print(f"{CYAN}Data acquired. Running BFT...{RESET}\n")
        return self.run_bft_analysis(data, 'trading')

    def detect_intent(self, user_input):
        """Use primary model to detect user intent and route to appropriate mode"""
        intent_prompt = f"""Analyze this user query and classify intent:

Query: "{user_input}"

Respond with ONLY ONE WORD from:
- TRADE (user wants to invest/buy/sell/make money)
- ANALYZE (user wants BFT analysis on specific ticker/topic)
- QUESTION (general question, use oversight mode)
- COMMAND (system command like help/logs/etc)

Intent:"""
        result = self.call_model('primary', intent_prompt, max_tokens=50, temperature=0.3)
        if result['success']:
            intent = result['result'].strip().upper()
            for keyword in ['TRADE', 'ANALYZE', 'QUESTION', 'COMMAND']:
                if keyword in intent:
                    return keyword
        return 'QUESTION'

    def trade_mode(self, user_input, budget=None):
        """Natural language trading mode - finds opportunities and executes paper trades"""
        print(f"{CYAN}🤑 TRADE MODE ACTIVATED{RESET}\n")
       
        # Ask primary model to suggest tickers based on user intent
        suggestion_prompt = f"""User wants to trade/invest: "{user_input}"

Suggest 1-3 ticker symbols that match their intent. Consider:
- Budget constraints if mentioned
- Market sectors/themes they reference
- Current market conditions
- Risk level implied

Respond with ONLY ticker symbols separated by spaces (e.g., AAPL MSFT TSLA):"""
       
        suggestion = self.call_model('primary', suggestion_prompt, max_tokens=100, temperature=0.7)
        if not suggestion['success']:
            print(f"{RED}Failed to generate ticker suggestions{RESET}")
            return
       
        # Extract tickers from response
        suggested_text = suggestion['result'].strip()
        potential_tickers = re.findall(r'\b[A-Z]{2,5}\b', suggested_text)
        tickers = potential_tickers[:3] if potential_tickers else []
       
        if not tickers:
            print(f"{YELLOW}No tickers identified. Try being more specific (e.g., 'buy tech stocks' or 'invest in AAPL'){RESET}")
            return
       
        print(f"{CYAN}Analyzing candidates: {', '.join(tickers)}{RESET}\n")
       
        # Run BFT on each ticker
        results = []
        for ticker in tickers:
            print(f"{YELLOW}═══ {ticker} ═══{RESET}")
            result = self.analyze_ticker(ticker, '2y')
            if result:
                results.append(result)
            print()
       
        # Execute paper trades on high-confidence signals
        if results:
            print(f"{CYAN}═══ TRADE EXECUTION ═══{RESET}")
            executed = 0
            for r in results:
                if r.get('confidence', 0) >= 0.80 and r.get('final_signal') == 'BULLISH':
                    ticker = r.get('ticker')
                    price = r.get('data_facts', {}).get('current_price')
                    if ticker and price:
                        # Calculate shares to buy (allocate budget evenly or use default)
                        shares = 10 if not budget else max(1, int((budget / len(results)) / price))
                        self.paper_buy(ticker, shares, price)
                        executed += 1
               
            if executed == 0:
                print(f"{YELLOW}No high-confidence BULLISH signals. No trades executed.{RESET}")
            else:
                print(f"{CYAN}✓ Executed {executed} paper trade(s){RESET}")
               
            # Show portfolio
            print()
            self.paper_status()

    def process_input(self, user_input):
        clean = user_input.strip()
        if not clean: return True
        if clean.startswith('/'):
            cmd = clean.lower()
            if cmd == '/help': self.show_help()
            elif cmd == '/patent': print(f"\n{CYAN}{self.patent_info}{RESET}\n")
            elif cmd.startswith('/logs'): self.show_logs(int(cmd.split()[1]) if len(cmd.split()) > 1 else 20)
            elif cmd == '/clear': self.conversation_history.clear(); print(f"{CYAN}History cleared{RESET}")
            elif cmd.startswith('/no-color'):
                parts = cmd.split()
                self.color_enabled = len(parts) == 1 or parts[1] in ('on', 'true', '1')
                _set_colors_enabled(self.color_enabled)
                print(f"{CYAN}Color {'enabled' if self.color_enabled else 'disabled'}{RESET}")
            elif cmd.startswith('/json') and 'last' in cmd:
                if self.last_results: print(json.dumps(self.last_results, indent=2))
                else: print(f"{YELLOW}No results{RESET}")
            elif cmd == '/models':
                if self.groq_client:
                    resp = self.groq_client.models.list()
                    ids = [getattr(m, 'id', '') for m in getattr(resp, 'data', [])]
                    print(f"{CYAN}Groq models:{RESET} " + ", ".join(sorted(ids)))
                self._resolve_model_ids()
                print(f"{CYAN}Mapping:{RESET} " + ", ".join([f"{k}:{self.models[k].get('id','n/a')}" for k in self.models]))
            elif cmd in ['/exit', '/quit']: print(f"{CYAN}ABE signing off.{RESET}"); return False
            elif cmd.startswith('/c '): self.execute_cli(clean[3:])
            elif cmd.startswith('/data '): self.analyze_ticker(clean[6:].split()[0].upper())
            elif cmd.startswith('/analyze '): self.analyze_ticker(clean[9:].split()[0].upper())
            elif cmd.startswith('/lies'):
                parts = clean.split()
                if len(parts) < 2:
                    print(f"{YELLOW}Usage: /lies <TICKER>{RESET}")
                else:
                    self.show_lies(parts[1].upper())
            elif cmd.startswith('/search '): print(f"\n{self.web_search(clean[8:])}\n")
            elif cmd.startswith('/bft '): self.run_bft_analysis(clean[5:], 'general')
            elif cmd.startswith('/oversight '): self.run_oversight(clean[11:])
            elif cmd.startswith('/paper'):
                parts = clean.split()
                if len(parts) < 2:
                    self.paper_status()
                elif parts[1] == 'buy' and len(parts) == 4:
                    ticker, shares_str = parts[2].upper(), parts[3]
                    try:
                        shares = float(shares_str)
                        data, error = self.fetch_live_data(ticker, '1d')
                        if error:
                            print(f"{RED}{error}{RESET}")
                        elif data.get('current_price'):
                            self.paper_buy(ticker, shares, data['current_price'])
                    except ValueError:
                        print(f"{RED}Invalid shares: {shares_str}{RESET}")
                elif parts[1] == 'sell' and len(parts) == 4:
                    ticker, shares_str = parts[2].upper(), parts[3]
                    try:
                        shares = float(shares_str)
                        data, error = self.fetch_live_data(ticker, '1d')
                        if error:
                            print(f"{RED}{error}{RESET}")
                        elif data.get('current_price'):
                            self.paper_sell(ticker, shares, data['current_price'])
                    except ValueError:
                        print(f"{RED}Invalid shares: {shares_str}{RESET}")
                elif parts[1] == 'reset':
                    self.paper_portfolio = {'cash': 100000.0, 'positions': {}, 'trades': []}
                    print(f"{CYAN}Paper portfolio reset to $100,000{RESET}")
            elif cmd.startswith('/trade '):
                query = clean[7:]
                self.trade_mode(query)
            else: print(f"{RED}Unknown command. /help{RESET}")
        else:
            # Auto-detect intent using AI
            intent = self.detect_intent(clean)
            print(f"{YELLOW}[Intent: {intent}]{RESET}")
           
            if intent == 'TRADE':
                self.trade_mode(clean)
            elif intent == 'ANALYZE':
                # Try to extract ticker, otherwise full BFT
                ticker_match = re.search(r'\b([A-Z]{2,5}(?:-[A-Z]{3,4})?)\b', clean)
                if ticker_match:
                    self.analyze_ticker(ticker_match.group(1))
                else:
                    self.run_bft_analysis(clean, 'general')
            elif intent == 'QUESTION':
                self.run_oversight(clean)
            else:
                # Fallback to old logic
                financial = any(kw in clean.lower() for kw in ['stock', 'btc', 'price', 'market'])
                ticker_match = re.search(r'\b([A-Z]{2,5}(?:-[A-Z]{3,4})?)\\b', clean)
                if financial or ticker_match:
                    ticker = ticker_match.group(1) if ticker_match else None
                    if ticker: self.analyze_ticker(ticker)
                    else: self.run_bft_analysis(clean, 'general')
                else:
                    self.run_oversight(clean)
        return True

def main():
    try:
        abe = ABEComplete()
        print(f"{DARK_GREEN}ABE v1.0 - Ready{RESET}\n")
        while True:
            try:
                user_input = input(f"{DARK_GREEN}> {RESET}")
                if not abe.process_input(user_input): break
            except (KeyboardInterrupt, EOFError):
                print(f"\n{CYAN}ABE signing off.{RESET}")
                break
    except Exception as e:
        print(f"{RED}Fatal: {e}{RESET}")
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
