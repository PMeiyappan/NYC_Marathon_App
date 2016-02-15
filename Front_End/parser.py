#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generic visualization package by Seth Brown
Modified and adapted for this project by Prasanth Meiyappan
Python 2.7.6
Last Modified: 2016-02-01
"""
from __future__ import print_function, division, absolute_import
import sys
import json
from itertools import izip_longest
from collections import defaultdict


def grouper(iterable, n, fillvalue=None):
    """ Read rows of data in groups of size n
    """
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)


def field_labels(label_row, datum_row):
    """ Match field labels with the appropriate data fields
        -> returns a dict of: {label: value, label: value...}
    """
    return dict(zip(label_row, datum_row))


def read(stdin):
    """ Pre-process data prior to parsing: strip whitespace/EOLs and split
        fields on tab delimiter
    """
    return (map(lambda r: r.strip(), _.strip().split('\t')) for _ in stdin)


def map_union(*args):
    """ Combine data maps into one dictionary; keys are assumed to be unique
    """
    union = {}
    for d in args:
        union.update(d)
    return union


def split_format(splits):
    """ Format split time strings
    """
    fmt_splits = []
    for split_idx, (split_label, split_str, dist) in enumerate(splits):
        comps = split_str.split(':')
        # if some splits are missing data (from original NYC data file)
        if len(comps) == 3:
            comps = map(int, comps)
            split_mins = comps[0]*60 + comps[1] + comps[2]/60
            datum = {'split_label': split_label, 'split_str': split_str,
                     'split_mins': split_mins, 'split_idx': split_idx,
                     'split_dist': dist}
        else:
            datum = {'split_label': split_label, 'split_str': '--',
                     'split_mins': '--', 'split_idx': split_idx,
                     'split_dist': dist}
        fmt_splits.append(datum)

    return fmt_splits


def parse(rows):
    """ Combine data rows into one data structure for each runner
    """
    compiled_data = []
    for row in grouper(rows, 5):
        row1_fields = ('year', 'id', 'name', 'age', 'sex', 'city', 'st', 'co')
        row2_fields = ('pace', 'proj_time', 'offl_time', 'place')
        split_fields = ('5k', '10k', '15k', '20k', 'Half', '25k',
                        '30k', '35k', '40k', 'Pre-Finish', 'Finish')
        
        row1 = field_labels(row1_fields, row[0])
        row2 = field_labels(row2_fields, row[4][0:4])

        times = row[2] + [row2['offl_time'], row2['offl_time']]
        dists = [5, 10, 15, 20, 21.097494, 25, 30, 35, 40, 42.194, 42.195]
        split_data = zip(split_fields, times, dists)
        fmt_splits = {'splits': split_format(split_data)}
        datum = map_union(row1, row2, fmt_splits)
        compiled_data.append(datum)

    return compiled_data


def find_rank(runner_idx, split_group):
    for runner in split_group:
        if runner['runner_idx'] == runner_idx:
            return runner['rank']


def name_format(name):
    """ Format runner names from 'John, Doe' to 'John Doe'
    """
    lst_name, fst_name = name.split(',')
    return ' '.join((fst_name, lst_name))


def place_at_splits(data):
    """ Find the overall place of each runner at each split across all years
    """
    groups = defaultdict(list)
    for runner_idx, runner in enumerate(data):
        splits = runner['splits']
        for split in splits:
            split['runner_idx'] = runner_idx
            groups[split['split_dist']].append(split)

    ranks = []
    srt_keys = sorted(groups, key=groups.get)
    for key in srt_keys:
        group = groups[key]
        srt_group = sorted(group, key=lambda t: t['split_mins'])
        ranked_group = []
        for rank, split in enumerate(srt_group):
            split['rank'] = rank
            ranked_group.append(split)
        ranks.append(ranked_group)

    return data, ranks


def impute(data, ranks):
    """ iterate over the ranks and for missing splits, impute the rank with
        with the runner's rank at the next split. using this new rank, rerank
        all the runners to preserve the adjusted rank.
    """
    rank_dict = {}
    for i, split in enumerate(ranks):
        for j, runner in enumerate(split):
            if runner['split_mins'] == '--':
                adj_rank = find_rank(runner['runner_idx'], ranks[i+1])
                runner['rank'] = adj_rank
                split[i][j] = runner

        srt_splits = sorted(split, key=lambda t: t['rank'])
        for r, runner in enumerate(srt_splits):
            runner['rank'] = r
            ridx = runner['runner_idx']
            label = runner['split_label']
            key = '{0}_{1}'.format(ridx, label)
            rank_dict[key] = runner

    for runner_idx, runner in enumerate(data):
        runner['name'] = name_format(runner['name'])
        year = int(runner['year'])
        splits = runner['splits']
        for n, split in enumerate(splits):
            key = '{0}_{1}'.format(runner_idx, split['split_label'])
            split['split_place'] = rank_dict[key]['rank']
            split['year'] = year

    return data


def to_json(d, filename):
    """ save parsed data to json file
    """
    with open(filename, 'wb') as outfile:
        json.dump(d, outfile, indent=4)


def main():
    rows = read(sys.stdin)
    data = parse(rows)
    placed_data, ranks = place_at_splits(data)
    impute_placed_data = impute(placed_data, ranks)
    to_json(impute_placed_data, sys.argv[1])


if __name__ == '__main__':
    main()
