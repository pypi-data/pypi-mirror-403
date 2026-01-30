import datasets
from torchmetrics.classification import JaccardIndex
from torchvision.transforms.v2.functional import pil_to_tensor

TAXONOMIES = {
    'cityscapes': {
        'num_classes': 19,
        'label_col': 'label',
        'gt_offset': 0
    },
    'ade20k': {
        'num_classes': 150,
        'label_col': 'annotation',
        'gt_offset': -1
    },
}

def evaluate_miou(model_fn, taxonomy, dataset):
    cfg = taxonomy if isinstance(taxonomy, dict) else TAXONOMIES[taxonomy]
    ds = datasets.load_dataset(dataset, split='validation')
    result = ds.map(model_fn).cast_column('pred', datasets.Image())
    metric = JaccardIndex(
        task="multiclass",
        num_classes=cfg['num_classes'],
        average="macro",
        ignore_index=255)
    for s in result:
        pred = pil_to_tensor(s['pred'])
        gt = pil_to_tensor(s[cfg['label_col']]) + cfg['gt_offset']
        metric.update(pred, gt)
    return result, metric.compute().item()