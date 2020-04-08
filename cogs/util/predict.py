from collections import defaultdict
import itertools
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

        self.avgs = defaultdict(lambda: [])

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

        for match in data:
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

    def simulate_matches(self):
        sku_avg = defaultdict(lambda: [])
        for i in self.matches:
            sku_avg[i["sku"]].append(i["redscore"])
            sku_avg[i["sku"]].append(i["bluescore"])
        sku_avg = {
            k: sum(v) / len(v)
            for k, v in sku_avg.items()
        }

        self.locked = True
        self.lock_start = time.time()
        self.avgs.clear()
        for i in self.matches:
            r1, r2 = i["red1"], i["red2"]
            b1, b2 = i["blue1"], i["blue2"]
            m2 = (i["redscore"] - i["bluescore"]) / sku_avg[i["sku"]]
            bs = i["bluescore"]
            rs = i["redscore"]

            bb = -m2 / (i["redscore"] or 1)
            rb = m2 / (i["bluescore"] or 1)

            self.avgs[r1].append((rs, rb))
            self.avgs[r2].append((rs, rb))
            self.avgs[b1].append((bs, bb))
            self.avgs[b2].append((bs, bb))
        for i in self.avgs:
            self.avgs[i] = (
                sum(j[0] for j in self.avgs[i]) / len(self.avgs[i]),
                sum(j[1] for j in self.avgs[i]) / len(self.avgs[i])
            )
        self.locked = False

    def predict_scores(self, red, blue):
        rs = sum(i[0] for i in red) / len(red)
        bs = sum(i[0] for i in blue) / len(blue)
        rb = sum(i[1] for i in red) / len(red)
        bb = sum(i[1] for i in blue) / len(blue)
        nrs = rs - rb * rs
        bs -= bb * bs
        return (nrs, bs)

    def generate_leaderboard(self):
        return sorted(
            self.avgs.keys(), key=lambda x: self.avgs[x][0],
            reverse=True
        )

    def compare(self, red, blue):
        red, blue = red.upper().split(','), blue.upper().split(',')

        for i in red:
            if i in blue:
                return ('A team cannot be in both alliances; that makes no sense', None)

        for i in red + blue:
            if i not in self.avgs:
                return (f'Unknown team: {i}', None)

        red = [self.avgs[i] for i in red]
        blue = [self.avgs[i] for i in blue]

        red_score, blue_score = self.predict_scores(red, blue)
        red_score = round(red_score)
        blue_score = round(blue_score)

        return red_score, blue_score


if __name__ == '__main__':
    Predictor().main()
