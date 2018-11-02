import itertools
import trueskill
import json
import math


class Predictor:
    DATA_FILE = 'data.json'
    TEAMS = ['red1', 'red2', 'blue1', 'blue2']

    def __init__(self):
        self.teams = {}
        self.matches = []

        self.populate_matches()
        self.populate_teams()

        print(f'{len(self.matches)} matches, {len(self.teams)} teams found')
        print(f'Simulating {len(self.matches)} matches..')

        self.simulate_matches()
        # self.print_leaderboard()

        # self.test_accuracy()

    def populate_matches(self):
        with open(self.DATA_FILE) as data_file:
            match_data = json.load(data_file)

        for i in match_data:
            for j in match_data[i]:
                if j['redscore'] == 0 and j['bluescore'] == 0:
                    # Assume the data hasn't been uploaded
                    continue
                self.matches.append(j)

    def populate_teams(self):
        for match in self.matches:
            for team in self.TEAMS:
                if match[team] and match[team] not in self.teams:
                    self.teams[match[team]] = trueskill.Rating()

    def simulate_matches(self):
        for n, match in enumerate(self.matches):
            print(f'\r  :: {n + 1} / {len(self.matches)}', end='')

            red_ts, red_names = [], []
            blue_ts, blue_names = [], []
            for i in self.TEAMS:
                name = match[i]
                if name:
                    if i.startswith('red'):
                        red_ts.append(self.teams[name])
                        red_names.append(name)
                    else:
                        blue_ts.append(self.teams[name])
                        blue_names.append(name)

            red_ts, blue_ts = trueskill.rate([red_ts, blue_ts],
                                             ranks=[match['bluescore'],
                                                    match['redscore']])

            tn = [*zip(red_ts, red_names)] + [*zip(blue_ts, blue_names)]
            for t, n in tn:
               self.teams[n] = t

        print()

    def win_probability(self, red, blue):
        delta_mu = sum(r.mu for r in red) - sum(r.mu for r in blue)
        sum_sigma = sum(r.sigma ** 2 for r in itertools.chain(red, blue))
        size = len(red) + len(blue)
        ts = trueskill.global_env()
        denom = math.sqrt(size * (ts.beta * ts.beta) + sum_sigma)
        return ts.cdf(delta_mu / denom)

    def generate_leaderboard(self):
        return sorted(
            self.teams.keys(), key=lambda x: trueskill.expose(self.teams[x]),
            reverse=True
        )

    def print_leaderboard(self):
        leaderboard = self.generate_leaderboard()

        printf('\r%r%i     ===== RESUTLS =====')
        for i in range(25):
            line = str(i + 1).rjust(4)
            line += ' | '
            line += (leaderboard[i] + ",").ljust(8)
            line += ' μ=' + str(round(self.teams[leaderboard[i]].mu, 1))
            line += ' σ=' + str(round(self.teams[leaderboard[i]].sigma, 2))

            print(line)

    def test_accuracy(self):
        success = []

        for n, match in enumerate(self.matches):
            print(f'\r  :: {n + 1} / {len(self.matches)}', end='')

            red, blue = [] , []
            for i in self.TEAMS:
                name = match[i]
                if name:
                    if i.startswith('red'):
                        red.append(self.teams[name])
                    else:
                        blue.append(self.teams[name])

            win_probability = self.win_probability(red, blue)

            if win_probability > 50:
                success.append(match['redscore'] > match['bluescore'])
            elif win_probability == 50:
                success.append(match['redscore'] == match['bluescore'])
            else:
                success.append(match['redscore'] < match['bluescore'])

        print()
        print(f'{round(sum(success) / len(success) * 100, 2)}%')

    def compare(self, red, blue):
        red, blue = red.split(','), blue.split(',')

        for i in red:
            if i in blue:
                return 'A team cannot be in both alliances; that makes no sense'

        for i in red + blue:
            if i not in self.teams:
                return 'Unknown team passed'

        red, blue = [self.teams[i] for i in red], [self.teams[i] for i in blue]

        win_probability = round(self.win_probability(red, blue) * 100, 2)

        if win_probability == 50:
            return 'I reccon it\'d be a perfect draw!'
        elif win_probability > 50:
            return f'I reccon red has a {win_probability}% chance of winning'
        else:
            return f'I reccon blue has a {100 - win_probability}% chance of winning'


if __name__ == '__main__':
    Predictor().main()
