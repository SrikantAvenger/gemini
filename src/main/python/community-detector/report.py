import argparse

import numpy
import pyarrow as pa
import pyarrow.parquet as pq

import community_detector


def read_connected_components(filepath):
    dict = pq.read_table(filepath).to_pydict()

    ccs = dict['cc']
    ids = dict['element_ids']
    return list(zip(ccs, ids))


def read_buckets_matrix(filepath):
    dict = pq.read_table(filepath).to_pydict()

    id_to_buckets = dict['buckets']

    return community_detector.build_matrix(id_to_buckets)


def main(dirpath):
    connected_components = read_connected_components('%s/cc.parquet' % dirpath)

    buckets_matrix = read_buckets_matrix('%s/buckets.parquet' % dirpath)
    n_ids = buckets_matrix.shape[0]

    # TODO (carlosms): Scala produces a map of cc->element-id,
    # the lib requires element-id->cc, but only to convert it
    # to cc->element-id. Easy change once everything is working.
    id_to_cc = community_detector.build_id_to_cc(connected_components, n_ids)

    # The result is a list of communities. Each community is a list of element-ids
    coms = community_detector.detect_communities(id_to_cc, buckets_matrix)
    com_ids = list(range(len(coms)))

    data = [pa.array(com_ids), pa.array(coms)]
    batch = pa.RecordBatch.from_arrays(data, ['community_id', 'element_ids'])

    table = pa.Table.from_batches([batch])
    pq.write_table(table, '%s/communities.parquet' % dirpath)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run community detection analysis.')
    parser.add_argument('path', help='directory path of the parquet files')
    args = parser.parse_args()

    main(args.path)
