import itertools
import trueskill
import asyncio
import time
import json
import math


class Predictor:
    DATA_FILE = 'data.json'
    TEAMS = ['red1', 'red2', 'blue1', 'blue2']

    MATCHES = 'https://api.vexdb.io/v1/get_matches?program=VRC&season=current&status=past'
    GET_TEAMS = 'https://api.vexdb.io/v1/get_teams?sku={}'
    LIMIT_START = '&limit_start={}'
    NODATA = '&nodata=true'

    def __init__(self, bot):
        self.bot = bot

        self.teams = {}
        self.matches = []

        self.skus = set()
        self.simulated = []

        self.populate_matches()
        self.populate_teams()

        print(f'{len(self.matches)} matches, {len(self.teams)} teams found')
        print(f'Simulating {len(self.matches)} matches..')
        self.lock_start = 0
        self.locked = False
        self.prog = None

        self.bot.loop.create_task(self.start_simulations())
        # self.simulate_matches()
        # self.print_leaderboard()

        # self.test_accuracy()

    async def get_matches(self, force=False):
        url = self.MATCHES
        async with self.bot.session.get(url + self.NODATA) as resp:
            count = (await resp.json())['size']

        data = []
        while len(data) < count:
            async with self.bot.session.get(url + self.LIMIT_START.format(len(data))) as resp:
                data += (await resp.json())['result']

        print(f'Found {len(data)} matches')
        matches = []
        skus = set()
        new_dat = {}

        for n, match in enumerate(data):
            if match['sku'] in self.skus and not force:
                continue
            if match['redscore'] == 0 and match['bluescore'] == 0:
                continue

            if match['sku'] not in new_dat:
                new_dat[match['sku']] = []
            new_dat[match['sku']].append(match)

            skus.add(match['sku'])
            matches.append(match)
        return skus, matches, new_dat

    async def get_teams_for_sku(self, sku):
        url = self.GET_TEAMS.format(sku)
        async with self.bot.session.get(url) as resp:
            data = (await resp.json())['result']
        return [
            i['number'] for i in data
        ]

    async def update_matches(self, ctx=None, force=False):
        skus, matches, new_dat = await self.get_matches(force)
        if force:
            self.skus = skus
            self.matches = matches
            old_dat = {}
        else:
            self.skus = self.skus.union(skus)
            self.matches += matches

            try:
                with open(self.DATA_FILE) as data_file:
                    old_dat = json.load(data_file)
            except FileNotFoundError:
                old_dat = {}

        if ctx is not None:
            await ctx.send(f'Found {len(skus)} new skus and {len(matches)} new matches.')

        def saver():
            old_dat.update(new_dat)
            with open(self.DATA_FILE, 'w') as data_file:
                json.dump(old_dat, data_file)
            self.populate_teams()

        await self.bot.loop.run_in_executor(None, saver)
        if ctx is not None:
            await ctx.send('Saved data and re-populated teams. Begining simulation.')

        await self.start_simulations()
        if ctx is not None:
            await ctx.send('Finished simulation. Match data is now synced with robotevents!')

    async def start_simulations(self):
        executor = None  # concurrent.futures.ThreadPoolExecutor()
        await self.bot.loop.run_in_executor(executor, self.simulate_matches)

    def populate_matches(self):
        try:
            with open(self.DATA_FILE) as data_file:
                match_data = json.load(data_file)
        except FileNotFoundError:
            match_data = {}

        for i in match_data:
            self.skus.add(i)
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
        return
        self.locked = True
        self.lock_start = time.time()
        for n, match in enumerate(self.matches):
            # print(f'\r  :: {n + 1} / {len(self.matches)}', end='')

            if match in self.simulated:
                continue
            self.simulated.append(match)

            self.prog = f'{n + 1} / {len(self.matches)}'

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

            time.sleep(0)  # Allow asyncio to interrupt us if it wants to
            red_ts, blue_ts = trueskill.rate([red_ts, blue_ts],
                                             ranks=[match['bluescore'],
                                                    match['redscore']])

            tn = [*zip(red_ts, red_names)] + [*zip(blue_ts, blue_names)]
            for t, n in tn:
               self.teams[n] = t

        self.locked = False

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
