#!/usr/bin/env python3
"""
ODIBETS COMPLETE SOPHISTICATED PREDICTION SYSTEM - WITH ENHANCED BTTS ANALYSIS
- Full sophisticated model with double chance integration
- Pattern-based BTTS failure detection
- Prints compact BTTS report only
"""

# ==================== INSTALL DEPENDENCIES ====================
!apt-get update -qq
!wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
!echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
!apt-get update -qq
!apt-get install -y -qq google-chrome-stable
!pip install -q selenium webdriver-manager pandas numpy scikit-learn beautifulsoup4 requests

# ==================== IMPORTS ====================
import numpy as np
import pandas as pd
import json
import os
import time
import threading
import requests
import re
from bs4 import BeautifulSoup
from collections import defaultdict
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import warnings
warnings.filterwarnings('ignore')

# ==================== YOUR WORKING HISTORICAL SCRAPER ====================

class OdibetsHistoricalScraper:
    """Your working historical data scraper"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        self.base_url = "https://odibets.com/league"
        self.historical_file = "odibets_data/historical_matches.json"
        self.team_mapping = {
            'MANCHESTER REDS': 'Manchester Reds',
            'MANCHESTER BLUE': 'Manchester Blue',
            'LIVERPOOL': 'Liverpool',
            'LONDON REDS': 'London Reds',
            'LONDON BLUES': 'London Blues',
            'EVERTON': 'Everton',
            'BURNLEY': 'Burnley',
            'NEWCASTLE': 'Newcastle',
            'LEICESTER': 'Leicester',
            'SOUTHAMPTON': 'Southampton',
            'TOTTENHAM': 'Tottenham',
            'WEST HAM': 'West Ham',
            'WOLVES': 'Wolves',
            'BRIGHTON': 'Brighton',
            'PALACE': 'Palace',
            'ASTON V': 'Aston V',
            'SHEFFIELD U': 'Sheffield U',
            'FULHAM': 'Fulham',
            'LEEDS': 'Leeds',
            'WEST BROM': 'West Brom'
        }
        self.teams = list(self.team_mapping.values())

    def extract_all_matches(self):
        """Extract all historical matches"""
        url = f"{self.base_url}?br=1&tab=results"

        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            all_matches = []
            tables = soup.find_all('table')

            for table in tables:
                matches = self._extract_matches_from_table(table)
                all_matches.extend(matches)

            if all_matches:
                os.makedirs('odibets_data', exist_ok=True)
                with open(self.historical_file, 'w', encoding='utf-8') as f:
                    json.dump(all_matches, f, indent=2, ensure_ascii=False)

                return len(all_matches)
            return 0

        except Exception as e:
            return 0

    def _extract_matches_from_table(self, table):
        matches = []
        rows = table.find_all('tr')

        for row in rows:
            cells = row.find_all('td')
            if len(cells) == 3:
                home_team = cells[0].get_text(strip=True)
                score_text = cells[1].get_text(strip=True)
                away_team = cells[2].get_text(strip=True)

                if home_team == 'English League' or 'WEEK' in home_team:
                    continue

                if len(score_text) >= 2 and score_text[:2].isdigit():
                    home_score = int(score_text[0])
                    away_score = int(score_text[1])

                    home_team = self._clean_team_name(home_team)
                    away_team = self._clean_team_name(away_team)

                    if home_team and away_team:
                        matches.append({
                            'home_team': home_team,
                            'home_score': home_score,
                            'away_score': away_score,
                            'away_team': away_team,
                            'total_goals': home_score + away_score,
                            'result': 'HOME_WIN' if home_score > away_score else 'AWAY_WIN' if away_score > home_score else 'DRAW',
                            'timestamp': datetime.now().isoformat()
                        })
        return matches

    def _clean_team_name(self, name):
        name_upper = name.upper().strip()
        if name_upper in self.team_mapping:
            return self.team_mapping[name_upper]
        for key, value in self.team_mapping.items():
            if key in name_upper or name_upper in key:
                return value
        return None

# ==================== DATA LOADER ====================

class OdibetsDataLoader:
    def __init__(self):
        self.historical_file = "odibets_data/historical_matches.json"
        self.teams = [
            'Manchester Reds', 'Manchester Blue', 'Liverpool', 'London Reds', 'London Blues',
            'Everton', 'Burnley', 'Newcastle', 'Leicester', 'Southampton', 'Tottenham',
            'West Ham', 'Wolves', 'Brighton', 'Palace', 'Aston V', 'Sheffield U',
            'Fulham', 'Leeds', 'West Brom'
        ]
        self.team_stats = {}
        self.has_data = False
        self.total_matches = 0
        self.load_historical_data()

    def load_historical_data(self):
        if not os.path.exists(self.historical_file):
            self.has_data = False
            return

        with open(self.historical_file, 'r', encoding='utf-8') as f:
            matches = json.load(f)

        self.total_matches = len(matches)

        if len(matches) == 0:
            self.has_data = False
            return

        team_data = {team: {'goals': [], 'conceded': [], 'h2h': {}} for team in self.teams}

        for match in matches:
            home, away = match['home_team'], match['away_team']
            hs, as_ = match['home_score'], match['away_score']

            team_data[home]['goals'].append(hs)
            team_data[home]['conceded'].append(as_)
            team_data[away]['goals'].append(as_)
            team_data[away]['conceded'].append(hs)

            if home in self.teams and away in self.teams:
                if away not in team_data[home]['h2h']:
                    team_data[home]['h2h'][away] = []
                if home not in team_data[away]['h2h']:
                    team_data[away]['h2h'][home] = []
                team_data[home]['h2h'][away].append((hs, as_))
                team_data[away]['h2h'][home].append((as_, hs))

        for team, data in team_data.items():
            g = data['goals']
            c = data['conceded']
            if g:
                avg_scored = np.mean(g)
                avg_conceded = np.mean(c)
                attack = avg_scored / 1.2
                defense = avg_conceded / 1.2
                matches_count = len(g)
                last5_g = g[-5:]
                last5_c = c[-5:]
            else:
                continue

            self.team_stats[team] = {
                'attack': attack,
                'defense': defense,
                'matches': matches_count,
                'last5_goals': last5_g,
                'last5_conceded': last5_c,
                'h2h': data['h2h']
            }

        self.has_data = len(self.team_stats) > 0

    def get_team_stats(self, team):
        return self.team_stats.get(team)

# ==================== ENHANCED FOOTBALL GRAPH ====================

class EnhancedFootballGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = {
            'temporal': [], 'similarity': [], 'quality_similarity': [],
            'opponent': [], 'common_opponent': [], 'form_chain': [], 'performance_causal': []
        }
        self.node_features = {}
        self.edge_weights = {}
        self.node_metadata = {}
        self.team_stats = defaultdict(dict)

    def add_node(self, node_id, features, metadata):
        self.nodes[node_id] = features
        self.node_features[node_id] = features
        self.node_metadata[node_id] = metadata
        team = metadata['team']
        if 'matches' not in self.team_stats[team]:
            self.team_stats[team]['matches'] = []
        self.team_stats[team]['matches'].append(metadata)

    def add_edge(self, edge_type, source, target, weight=1.0):
        self.edges[edge_type].append((source, target))
        self.edge_weights[(source, target, edge_type)] = weight

    def extract_core_variables(self, team_A, team_B, data_loader):
        statsA = data_loader.get_team_stats(team_A)
        statsB = data_loader.get_team_stats(team_B)
        if not statsA or not statsB:
            return None
        s_A = np.mean(statsA['last5_goals']) if statsA['last5_goals'] else 1.0
        s_B = np.mean(statsB['last5_goals']) if statsB['last5_goals'] else 1.0
        h2hA = statsA['h2h'].get(team_B, [])
        h2hB = statsB['h2h'].get(team_A, [])
        h_AB = np.mean([g for g, _ in h2hA]) if h2hA else 1.0
        h_BA = np.mean([g for _, g in h2hB]) if h2hB else 1.0
        return {
            's_A': s_A, 's_B': s_B, 'h_AB': h_AB, 'h_BA': h_BA,
            'team_A_matches': statsA['matches'], 'team_B_matches': statsB['matches'],
            'h2h_matches': len(h2hA),
            'team_A_recent_form': self._recent_form(statsA),
            'team_B_recent_form': self._recent_form(statsB)
        }

    def _recent_form(self, stats):
        if stats['matches'] == 0:
            return 0.5
        return min(1.0, np.mean(stats['last5_goals']) / 2.0)

    def radical_inverse(self, c, base):
        result, f = 0.0, 1.0 / base
        while c > 0:
            c, digit = divmod(c, base)
            result += digit * f
            f /= base
        return result

    def first_n_primes(self, n):
        if n <= 0:
            return []
        primes, candidate = [2], 3
        while len(primes) < n:
            if all(candidate % p for p in primes if p * p <= candidate):
                primes.append(candidate)
            candidate += 2
        return primes

    def hammersley_points(self, K, n):
        primes = self.first_n_primes(n - 1)
        H = np.zeros((K, n))
        for k in range(1, K+1):
            H[k-1, 0] = k / K
            for j, p in enumerate(primes, start=1):
                H[k-1, j] = self.radical_inverse(k, p)
        return H

    def project_core_variables_to_hammersley(self, team_A, team_B, data_loader, K=4):
        core_vars = self.extract_core_variables(team_A, team_B, data_loader)
        if not core_vars:
            return 0.5
        core_array = np.array([core_vars['s_A'], core_vars['s_B'], core_vars['h_AB'], core_vars['h_BA']])
        normalized = core_array / 4.0
        hammersley_points = self.hammersley_points(K, 4)
        distances = np.linalg.norm(hammersley_points - normalized, axis=1)
        mean_dist = np.mean(distances)
        return 1.0 / (1.0 + mean_dist)

# ==================== FAST GRAPH BUILDER ====================

class FastGraphBuilder:
    def __init__(self, team_a, team_b, data_loader):
        self.team_a = team_a
        self.team_b = team_b
        self.data_loader = data_loader
        self.graph = EnhancedFootballGraph()

    def build(self):
        self._add_team_nodes(self.team_a)
        self._add_team_nodes(self.team_b)
        self._add_h2h_nodes()
        self._build_opponent_edges()
        self._build_temporal_edges()
        self._build_similarity_edges()
        return self.graph

    def _add_team_nodes(self, team):
        stats = self.data_loader.get_team_stats(team)
        if not stats:
            return
        for i, (g, c) in enumerate(zip(stats['last5_goals'], stats['last5_conceded'])):
            features = np.array([g, c, g - c])
            metadata = {
                'team': team, 'match_type': 'League', 'time': i,
                'is_home': i % 2 == 0, 'result': 1 if g > c else (0 if g == c else -1),
                'goals_scored': g, 'goals_conceded': c
            }
            self.graph.add_node(f"{team}_L{i}", features, metadata)

    def _add_h2h_nodes(self):
        statsA = self.data_loader.get_team_stats(self.team_a)
        if not statsA:
            return
        h2h = statsA['h2h'].get(self.team_b, [])
        for i, (g, c) in enumerate(h2h[-5:]):
            features = np.array([g, c, g - c])
            metadata = {
                'team': self.team_a, 'match_type': 'H2H', 'time': -i-1,
                'is_home': True, 'result': 1 if g > c else (0 if g == c else -1),
                'goals_scored': g, 'goals_conceded': c
            }
            self.graph.add_node(f"{self.team_a}_H{i}", features, metadata)

        statsB = self.data_loader.get_team_stats(self.team_b)
        if not statsB:
            return
        h2hB = statsB['h2h'].get(self.team_a, [])
        for i, (g, c) in enumerate(h2hB[-5:]):
            features = np.array([g, c, g - c])
            metadata = {
                'team': self.team_b, 'match_type': 'H2H', 'time': -i-1,
                'is_home': True, 'result': 1 if g > c else (0 if g == c else -1),
                'goals_scored': g, 'goals_conceded': c
            }
            self.graph.add_node(f"{self.team_b}_H{i}", features, metadata)

    def _build_opponent_edges(self):
        nodesA = [n for n in self.graph.nodes if n.startswith(self.team_a) and 'L' in n]
        nodesB = [n for n in self.graph.nodes if n.startswith(self.team_b) and 'L' in n]
        for na in nodesA:
            for nb in nodesB:
                self.graph.add_edge('opponent', na, nb, weight=1.0)

    def _build_temporal_edges(self):
        for team in [self.team_a, self.team_b]:
            nodes = []
            for n in self.graph.nodes:
                if n.startswith(team) and '_L' in n:
                    try:
                        idx = int(n.split('_L')[1])
                        nodes.append((n, idx))
                    except (IndexError, ValueError):
                        continue
            nodes.sort(key=lambda x: x[1])
            for i in range(len(nodes)-1):
                self.graph.add_edge('temporal', nodes[i][0], nodes[i+1][0], weight=1.0)

    def _build_similarity_edges(self):
        nodes = list(self.graph.nodes.keys())
        for i in range(len(nodes)):
            for j in range(i+1, len(nodes)):
                if self.graph.node_metadata[nodes[i]]['team'] == self.graph.node_metadata[nodes[j]]['team']:
                    feat_i = self.graph.node_features[nodes[i]]
                    feat_j = self.graph.node_features[nodes[j]]
                    sim = 1 - abs(feat_i[0] - feat_j[0]) / 4
                    if sim > 0.7:
                        self.graph.add_edge('similarity', nodes[i], nodes[j], weight=sim)

# ==================== BAYESIAN SCORE PREDICTOR ====================

class BayesianScorePredictor:
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.league_avg = 1.2
        self.home_adv = 0.3

    def predict_goals_with_uncertainty(self, team_a, team_b, is_home=True):
        statsA = self.data_loader.get_team_stats(team_a)
        statsB = self.data_loader.get_team_stats(team_b)
        if not statsA or not statsB:
            return None

        attackA = statsA['attack']
        defenseA = statsA['defense']
        attackB = statsB['attack']
        defenseB = statsB['defense']

        lambda_a = self.league_avg * attackA * defenseB
        lambda_b = self.league_avg * attackB * defenseA
        if is_home:
            lambda_a *= (1 + self.home_adv)
            lambda_b *= (1 - self.home_adv * 0.5)
        else:
            lambda_a *= (1 - self.home_adv * 0.5)
            lambda_b *= (1 + self.home_adv)

        n_samples = 10000
        goals_a = np.random.poisson(lambda_a, n_samples)
        goals_b = np.random.poisson(lambda_b, n_samples)

        return {
            team_a: {
                'expected_goals': round(np.mean(goals_a), 2),
                'uncertainty': round(np.std(goals_a), 2),
                'confidence_67_interval': [int(np.percentile(goals_a, 16.5)), int(np.percentile(goals_a, 83.5))],
                'goal_probabilities': {
                    '0_goals': np.mean(goals_a == 0),
                    '1_goal': np.mean(goals_a == 1),
                    '2_goals': np.mean(goals_a == 2),
                    '3+_goals': np.mean(goals_a >= 3)
                },
                'distribution_samples': goals_a
            },
            team_b: {
                'expected_goals': round(np.mean(goals_b), 2),
                'uncertainty': round(np.std(goals_b), 2),
                'confidence_67_interval': [int(np.percentile(goals_b, 16.5)), int(np.percentile(goals_b, 83.5))],
                'goal_probabilities': {
                    '0_goals': np.mean(goals_b == 0),
                    '1_goal': np.mean(goals_b == 1),
                    '2_goals': np.mean(goals_b == 2),
                    '3+_goals': np.mean(goals_b >= 3)
                },
                'distribution_samples': goals_b
            }
        }

# ==================== PROBABILISTIC OUTCOME PREDICTOR ====================

class ProbabilisticOutcomePredictor:
    def calculate_outcomes(self, score_pred):
        if not score_pred:
            return None

        team_a = list(score_pred.keys())[0]
        team_b = list(score_pred.keys())[1]
        samples_a = score_pred[team_a]['distribution_samples']
        samples_b = score_pred[team_b]['distribution_samples']

        home_win = np.mean(samples_a > samples_b)
        draw = np.mean(samples_a == samples_b)
        away_win = np.mean(samples_a < samples_b)
        btts = np.mean((samples_a > 0) & (samples_b > 0))
        over_1_5 = np.mean(samples_a + samples_b > 1.5)
        over_2_5 = np.mean(samples_a + samples_b > 2.5)

        # Calculate correct scores
        score_counts = {}
        for a, b in zip(samples_a[:5000], samples_b[:5000]):
            score = (int(a), int(b))
            score_counts[score] = score_counts.get(score, 0) + 1

        total = len(samples_a[:5000])
        correct_scores = {f"{a}-{b}": round(c/total, 3) for (a, b), c in
                         sorted(score_counts.items(), key=lambda x: x[1], reverse=True)[:10]}

        return {
            'btts': {'probability': round(btts, 3)},
            '1x2': {
                'home_win': {'probability': round(home_win, 3)},
                'draw': {'probability': round(draw, 3)},
                'away_win': {'probability': round(away_win, 3)},
                'most_likely': 'HOME' if home_win > draw and home_win > away_win else
                              'DRAW' if draw > away_win else 'AWAY'
            },
            'correct_scores': correct_scores,
            'over_under': {'over_1.5': round(over_1_5, 3), 'over_2.5': round(over_2_5, 3)}
        }

# ==================== GRAPH-ENHANCED FEATURE ENGINE ====================

class GraphEnhancedFeatureEngine:
    def __init__(self, graph, data_loader):
        self.graph = graph
        self.data_loader = data_loader

    def extract_advanced_features(self, team_a, team_b, is_home=True):
        core_vars = self.graph.extract_core_variables(team_a, team_b, self.data_loader)
        if not core_vars:
            return {}

        features = {
            'attack_strength_a': core_vars['s_A'],
            'attack_strength_b': core_vars['s_B'],
            'h2h_advantage_a': core_vars['h_AB'],
            'h2h_advantage_b': core_vars['h_BA'],
            'form_momentum_a': core_vars['team_A_recent_form'],
            'form_momentum_b': core_vars['team_B_recent_form'],
            'data_completeness': min(1.0, (core_vars['team_A_matches'] + core_vars['team_B_matches']) / 20),
            'home_advantage': 1.0 if is_home else 0.0,
            'rivalry_strength': self._calculate_rivalry_strength(team_a, team_b),
        }

        features['hammersley_projection_quality'] = self.graph.project_core_variables_to_hammersley(
            team_a, team_b, self.data_loader)

        return features

    def _calculate_rivalry_strength(self, team_a, team_b):
        statsA = self.data_loader.get_team_stats(team_a)
        if not statsA:
            return 0.3
        h2h_matches = statsA['h2h'].get(team_b, [])
        if len(h2h_matches) < 3:
            return 0.3
        goal_differences = [abs(g - c) for g, c in h2h_matches]
        return 1.0 - min(np.mean(goal_differences) / 3.0, 1.0)

# ==================== MODEL CONFIDENCE CALCULATOR ====================

class ModelConfidenceCalculator:
    def __init__(self, graph, data_loader):
        self.graph = graph
        self.data_loader = data_loader

    def calculate_model_confidence(self, team_a, team_b, features, score_samples):
        if not score_samples:
            return {}

        statsA = self.data_loader.get_team_stats(team_a)
        statsB = self.data_loader.get_team_stats(team_b)

        if not statsA or not statsB:
            return {}

        team_a_matches = statsA['matches']
        team_b_matches = statsB['matches']
        h2h_matches = len(statsA['h2h'].get(team_b, []))

        min_league_matches = min(team_a_matches, team_b_matches)
        if min_league_matches >= 15:
            sample_factor = 1.0
        elif min_league_matches >= 10:
            sample_factor = 0.8
        elif min_league_matches >= 5:
            sample_factor = 0.6
        else:
            sample_factor = 0.3

        if h2h_matches >= 5:
            h2h_factor = 1.0
        elif h2h_matches >= 3:
            h2h_factor = 0.7
        elif h2h_matches >= 1:
            h2h_factor = 0.4
        else:
            h2h_factor = 0.1

        data_quality = (sample_factor + h2h_factor) / 2

        samples_a = list(score_samples.values())[0]['distribution_samples']
        samples_b = list(score_samples.values())[1]['distribution_samples']
        bootstrap_probs = []
        for _ in range(50):
            idx = np.random.choice(len(samples_a), len(samples_a), replace=True)
            bs_prob = np.mean((samples_a[idx] > 0) & (samples_b[idx] > 0))
            bootstrap_probs.append(bs_prob)

        stability = 1.0 - min(1.0, np.std(bootstrap_probs) / max(np.mean(bootstrap_probs), 0.01))

        feature_reliability = features.get('hammersley_projection_quality', 0.5)

        overall = data_quality * 0.4 + stability * 0.3 + feature_reliability * 0.3

        if overall >= 0.8:
            level = "VERY HIGH"
        elif overall >= 0.7:
            level = "HIGH"
        elif overall >= 0.6:
            level = "MEDIUM HIGH"
        elif overall >= 0.5:
            level = "MEDIUM"
        elif overall >= 0.4:
            level = "MEDIUM LOW"
        elif overall >= 0.3:
            level = "LOW"
        else:
            level = "VERY LOW"

        return {
            'overall_confidence': round(overall, 3),
            'confidence_level': level,
            'factor_breakdown': {
                'data_quality': round(data_quality, 3),
                'model_stability': round(stability, 3),
                'feature_reliability': round(feature_reliability, 3),
                'historical_accuracy': 0.7
            }
        }

# ==================== SOPHISTICATED PREDICTION ENGINE ====================

class SophisticatedPredictionEngine:
    def __init__(self, football_graph, data_loader):
        self.graph = football_graph
        self.data_loader = data_loader
        self.bayesian_predictor = BayesianScorePredictor(data_loader)
        self.outcome_predictor = ProbabilisticOutcomePredictor()
        self.feature_engine = GraphEnhancedFeatureEngine(football_graph, data_loader)
        self.confidence_calculator = ModelConfidenceCalculator(football_graph, data_loader)

    def predict_match(self, team_a, team_b, home_team=None):
        is_home = (home_team == team_a) if home_team else True

        features = self.feature_engine.extract_advanced_features(team_a, team_b, is_home)
        if not features:
            return None

        score_prediction = self.bayesian_predictor.predict_goals_with_uncertainty(team_a, team_b, is_home)
        if not score_prediction:
            return None

        outcome_prediction = self.outcome_predictor.calculate_outcomes(score_prediction)
        confidence = self.confidence_calculator.calculate_model_confidence(team_a, team_b, features, score_prediction)
        core_vars = self.graph.extract_core_variables(team_a, team_b, self.data_loader)

        insights = []
        if features.get('attack_strength_a', 0) > features.get('attack_strength_b', 0) + 0.5:
            insights.append(f"{team_a} has significantly stronger attack")
        elif features.get('attack_strength_b', 0) > features.get('attack_strength_a', 0) + 0.5:
            insights.append(f"{team_b} has significantly stronger attack")

        if features.get('form_momentum_a', 0) > features.get('form_momentum_b', 0) + 0.2:
            insights.append(f"{team_a} has better recent form")
        elif features.get('form_momentum_b', 0) > features.get('form_momentum_a', 0) + 0.2:
            insights.append(f"{team_b} has better recent form")

        if features.get('h2h_advantage_a', 0) > features.get('h2h_advantage_b', 0) + 0.3:
            insights.append(f"{team_a} has strong H2H advantage")
        elif features.get('h2h_advantage_b', 0) > features.get('h2h_advantage_a', 0) + 0.3:
            insights.append(f"{team_b} has strong H2H advantage")

        if features.get('rivalry_strength', 0) > 0.7:
            insights.append("High rivalry match - expect competitive game")

        return {
            'match': f"{team_a} vs {team_b}",
            'context': {
                'home_team': team_a if is_home else team_b,
                'away_team': team_b if is_home else team_a,
                'data_quality': features.get('data_completeness', 0),
                'rivalry_strength': features.get('rivalry_strength', 0)
            },
            'score_prediction': score_prediction,
            'outcome_prediction': outcome_prediction,
            'model_confidence': confidence,
            'feature_analysis': {
                'key_features': insights,
                'hammersley_quality': features.get('hammersley_projection_quality', 0)
            },
            'core_variables': core_vars
        }

# ==================== ENHANCED BTTS ANALYZER ====================

class EnhancedBTTSAnalyzer:
    """Pattern-based BTTS analyzer with double chance integration"""

    def __init__(self):
        self.thresholds = {
            'high_zero_goal_risk': 0.35,
            'moderate_zero_goal_risk': 0.30,
            'attack_imbalance_ratio': 1.5,
            'h2h_low_goals': 1.5,
            'form_critical': 0.3,
            'btts_prob_critical': 0.50,
        }

    def analyze_btts(self, pred):
        """Complete BTTS analysis with pattern detection and double chance"""

        match = pred['match']
        home_team, away_team = match.split(' vs ')

        score_pred = pred['score_prediction']
        home_data = score_pred[home_team]
        away_data = score_pred[away_team]

        home_zero_prob = home_data['goal_probabilities']['0_goals']
        away_zero_prob = away_data['goal_probabilities']['0_goals']
        home_xg = home_data['expected_goals']
        away_xg = away_data['expected_goals']

        core = pred['core_variables']
        home_form = core.get('team_A_recent_form', 0.5) if core else 0.5
        away_form = core.get('team_B_recent_form', 0.5) if core else 0.5
        h2h_matches = core.get('h2h_matches', 0) if core else 0
        h2h_avg = (core.get('h_AB', 1.0) + core.get('h_BA', 1.0)) / 2 if core else 2.0

        model_btts_prob = pred['outcome_prediction']['btts']['probability']

        # Get model confidence
        model_confidence = pred['model_confidence'].get('confidence_level', 'MEDIUM') if pred['model_confidence'] else 'MEDIUM'

        # Get 1x2 probabilities
        result = pred['outcome_prediction']['1x2']
        home_win_prob = result['home_win']['probability']
        draw_prob = result['draw']['probability']
        away_win_prob = result['away_win']['probability']

        # Calculate double chance
        double_1X = home_win_prob + draw_prob
        double_X2 = draw_prob + away_win_prob
        double_12 = home_win_prob + away_win_prob

        double_probs = {'1X': double_1X, 'X2': double_X2, '12': double_12}
        most_likely_double = max(double_probs, key=double_probs.get)

        # Risk scoring
        risk_factors = []
        risk_score = 0

        # Pattern 1: Zero goal probability
        if away_zero_prob >= self.thresholds['high_zero_goal_risk']:
            risk_factors.append(f"{away_team} has {away_zero_prob:.0%} chance to score 0")
            risk_score += 3
        elif away_zero_prob >= self.thresholds['moderate_zero_goal_risk']:
            risk_factors.append(f"{away_team} has {away_zero_prob:.0%} chance to score 0 (borderline)")
            risk_score += 1

        if home_zero_prob >= self.thresholds['high_zero_goal_risk']:
            risk_factors.append(f"{home_team} has {home_zero_prob:.0%} chance to score 0")
            risk_score += 3
        elif home_zero_prob >= self.thresholds['moderate_zero_goal_risk']:
            risk_factors.append(f"{home_team} has {home_zero_prob:.0%} chance to score 0 (borderline)")
            risk_score += 1

        # Pattern 2: Attack imbalance
        if home_xg / away_xg >= self.thresholds['attack_imbalance_ratio']:
            risk_factors.append(f"{home_team} attack is {home_xg/away_xg:.1f}x stronger")
            risk_score += 2
        elif away_xg / home_xg >= self.thresholds['attack_imbalance_ratio']:
            risk_factors.append(f"{away_team} attack is {away_xg/home_xg:.1f}x stronger")
            risk_score += 2

        # Pattern 3: H2H low-scoring
        if h2h_matches >= 2 and h2h_avg < self.thresholds['h2h_low_goals']:
            risk_factors.append(f"H2H average only {h2h_avg:.1f} goals per match")
            risk_score += 2

        # Pattern 4: Poor form
        if away_form < self.thresholds['form_critical']:
            risk_factors.append(f"{away_team} recent form very poor ({away_form:.0%})")
            risk_score += 2
        if home_form < self.thresholds['form_critical']:
            risk_factors.append(f"{home_team} recent form very poor ({home_form:.0%})")
            risk_score += 2

        # Pattern 5: Double chance analysis
        double_insights = []
        if most_likely_double == '12':
            double_insights.append(f"Double chance 12 ({double_probs['12']:.1%}) suggests open game")
            if double_probs['12'] > 0.70:
                risk_score -= 1  # Reduces risk
        else:
            double_insights.append(f"Double chance {most_likely_double} ({double_probs[most_likely_double]:.1%}) suggests cautious game")
            risk_score += 2

        # Make final prediction
        if risk_score >= 5:
            final_prediction = "NO"
            confidence = "HIGH"
            reasoning = f"Multiple failure patterns detected (risk score: {risk_score})"
        elif risk_score >= 3:
            final_prediction = "NO"
            confidence = "MODERATE"
            reasoning = f"Several risk patterns present (risk score: {risk_score})"
        elif risk_score >= 1 and model_btts_prob < 0.55:
            final_prediction = "NO"
            confidence = "LOW"
            reasoning = f"Risk patterns with borderline probability (risk score: {risk_score})"
        else:
            final_prediction = "YES"
            confidence = "MODERATE" if risk_score > 0 else "HIGH"
            reasoning = f"No significant risk patterns detected (risk score: {risk_score})"

        return {
            'match': match,
            'home_team': home_team,
            'away_team': away_team,
            'final_prediction': final_prediction,
            'model_probability': model_btts_prob,
            'confidence': confidence,
            'model_confidence': model_confidence,
            'reasoning': reasoning,
            'risk_factors': risk_factors,
            'double_chance': {
                '1X': double_1X,
                'X2': double_X2,
                '12': double_12,
                'most_likely': most_likely_double
            },
            'double_insights': double_insights,
            'key_metrics': {
                f"{home_team}_zero_prob": home_zero_prob,
                f"{away_team}_zero_prob": away_zero_prob,
                f"{home_team}_xg": home_xg,
                f"{away_team}_xg": away_xg,
                f"{home_team}_form": home_form,
                f"{away_team}_form": away_form,
                'h2h_avg_goals': h2h_avg,
                'h2h_matches': h2h_matches
            }
        }

# ==================== SELENIUM MANAGER ====================

class SeleniumManager:
    def __init__(self):
        self.driver = None
        self.matchups_cache = None
        self.cache_time = 0
        self.max_retries = 3

    def start(self):
        for attempt in range(self.max_retries):
            try:
                chrome_options = Options()
                chrome_options.add_argument('--headless=new')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--window-size=1920,1080')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.binary_location = "/usr/bin/google-chrome"

                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.set_page_load_timeout(20)
                print("✓ Chrome started")
                return True
            except Exception as e:
                print(f"Chrome start attempt {attempt + 1} failed")
                time.sleep(2)
        return False

    def get_next_games(self):
        if not self.driver:
            if not self.start():
                return None, []

        if self.matchups_cache and (time.time() - self.cache_time) < 30:
            current_times, matchups = self.matchups_cache
        else:
            for attempt in range(self.max_retries):
                try:
                    self.driver.get("https://odibets.com/league?br=1")
                    wait = WebDriverWait(self.driver, 15)
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "game")))
                    time.sleep(1)

                    page_text = self.driver.page_source
                    time_pattern = re.compile(r'\b(1[0-9]:[0-5][0-9]|2[0-3]:[0-5][0-9])\b')
                    all_times = list(dict.fromkeys(time_pattern.findall(page_text)))
                    current_times = [t for t in all_times if 10 <= int(t.split(':')[0]) <= 23]
                    current_times.sort()

                    if not current_times:
                        return None, []

                    first_time = current_times[0]
                    time_element = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{first_time}')]")
                    self.driver.execute_script("arguments[0].click();", time_element)
                    time.sleep(1)

                    game_elements = self.driver.find_elements(By.CSS_SELECTOR, ".game, .game.e")
                    matchups = []
                    for game in game_elements[:10]:
                        lines = game.text.split('\n')
                        if len(lines) >= 2:
                            home = lines[0].strip()
                            away = lines[1].strip()
                            if home and away and not home.isdigit():
                                matchups.append((home, away))

                    if not matchups:
                        return None, []

                    self.matchups_cache = (current_times, matchups)
                    self.cache_time = time.time()
                    break

                except TimeoutException:
                    if attempt == self.max_retries - 1:
                        return None, []
                    time.sleep(2)
                except Exception:
                    if attempt == self.max_retries - 1:
                        return None, []
                    time.sleep(2)

        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute

        next_time = None
        for ts in current_times:
            h, m = map(int, ts.split(':'))
            if h > current_hour or (h == current_hour and m >= current_minute):
                next_time = ts
                break

        if not next_time:
            next_time = current_times[0]

        next_games = []
        for home, away in matchups:
            next_games.append({'home_team': home, 'away_team': away, 'time': next_time})

        return next_time, next_games

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
                print("✓ Chrome closed")
            except:
                pass

# ==================== COLLECTOR THREAD ====================

class HistoricalCollectorThread(threading.Thread):
    def __init__(self, historical_scraper, data_loader):
        super().__init__(daemon=True)
        self.historical_scraper = historical_scraper
        self.data_loader = data_loader
        self.running = True
        self.new_data_event = threading.Event()

    def run(self):
        while self.running:
            try:
                count = self.historical_scraper.extract_all_matches()
                if count > 0:
                    self.data_loader.load_historical_data()
                    self.new_data_event.set()
            except:
                pass
            time.sleep(60)

# ==================== COMPACT BTTS REPORT PRINTER ====================

def print_compact_btts_report(analysis, time_slot):
    """Print compact BTTS report with all double chance analysis included"""

    # Get double chance info
    dc = analysis['double_chance']

    # Get confidence info
    btts_confidence = analysis['confidence']
    model_confidence = analysis['model_confidence']

    # Create compact output with all double chance options
    print(f"{analysis['match']} | {time_slot} | DC: 1X({dc['1X']:.1%}) X2({dc['X2']:.1%}) 12({dc['12']:.1%}) [Most Likely: {dc['most_likely']}] | BTTS: {analysis['final_prediction']} ({analysis['model_probability']:.1%}) | Conf: {btts_confidence} | Model: {model_confidence}")

# ==================== MAIN ====================

def main():
    print("=" * 50)
    print("🚀 ODIBETS BTTS ANALYSIS SYSTEM")
    print("   Compact Mode - All Double Chance Options")
    print("=" * 50)

    print("\n📊 Collecting historical data...")
    historical_scraper = OdibetsHistoricalScraper()
    initial_count = historical_scraper.extract_all_matches()
    print(f"✓ Historical: {initial_count} matches")

    data_loader = OdibetsDataLoader()
    data_loader.load_historical_data()

    btts_analyzer = EnhancedBTTSAnalyzer()

    collector = HistoricalCollectorThread(historical_scraper, data_loader)
    collector.start()

    selenium_mgr = SeleniumManager()
    if not selenium_mgr.start():
        print("❌ Cannot continue without Chrome")
        return

    print("\n🔄 System running...")
    print("   Press Ctrl+C to stop\n")

    last_predicted_time = None

    try:
        while True:
            next_time, next_games = selenium_mgr.get_next_games()

            if next_games and next_time != last_predicted_time and data_loader.has_data:
                last_predicted_time = next_time

                for game in next_games:
                    home, away = game['home_team'], game['away_team']

                    stats_h = data_loader.get_team_stats(home)
                    stats_a = data_loader.get_team_stats(away)

                    if not stats_h or not stats_a:
                        print(f"⚠️ No stats available for {home} vs {away}")
                        continue

                    builder = FastGraphBuilder(home, away, data_loader)
                    graph = builder.build()
                    engine = SophisticatedPredictionEngine(graph, data_loader)
                    pred = engine.predict_match(home, away, home)

                    if pred:
                        analysis = btts_analyzer.analyze_btts(pred)
                        print_compact_btts_report(analysis, next_time)
                    else:
                        print(f"⚠️ Prediction failed for {home} vs {away}")

            if collector.new_data_event.is_set():
                collector.new_data_event.clear()
                print(f"\n📊 Historical data updated! Now: {data_loader.total_matches} matches")

            time.sleep(15)

    except KeyboardInterrupt:
        print("\n\n🛑 Stopping...")
        selenium_mgr.close()
        print("✅ System stopped")

if __name__ == "__main__":
    main()
