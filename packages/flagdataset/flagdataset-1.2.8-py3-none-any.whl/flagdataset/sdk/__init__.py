class S3Downloader:

    @staticmethod
    def download(dataset_id, target, prefix=None, key=None, jobs=4, debug=False, proxy=None):
        from ..core.baai_share_url import download_share
        from ..baai_config import config_read

        network = config_read().get("network") or "public"
        print(f"network: {network}")

        download_share(dataset_id, target, prefix, key, jobs_down=jobs, debug=debug, proxy=proxy, network=network)



def new_downloader(ak, sk, runtime="ks3util"):
    from ..baai_config import config_update
    from ..baai_environment import setup_network

    config_update({
        "ak": ak,
        "sk": sk,
    })

    setup_network()


    return S3Downloader()