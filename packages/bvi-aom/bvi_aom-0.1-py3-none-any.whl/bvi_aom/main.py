from typing import Union
import os 
import wget
import tarfile

class BVIAOMDataset:
    def __init__(self, storage_path: str, resolutions: Union[tuple[str], list[str], str], remove_tar: bool = False):
        allowed_resolutions = {'3840x2176', '1920x1088', '960x544', '480x272'}

        # Normalize resolutions to a list for validation
        if isinstance(resolutions, str):
            resolutions_to_check = [resolutions]
        elif isinstance(resolutions, (list, tuple)):
            resolutions_to_check = list(resolutions)
        else:
            raise TypeError("resolutions must be a string, list of strings, or tuple of strings.")

        for r in resolutions_to_check:
            if r not in allowed_resolutions:
                raise ValueError(f"Invalid resolution '{r}'. Allowed values are: {', '.join(allowed_resolutions)}")

        self.storage_path = storage_path
        self.resolutions = resolutions
        self.remove_tar = remove_tar
        self.cloud_links = {
            '3840x2176': ['http://download.opencontent.netflix.com.s3.amazonaws.com/bvi_aom_dataset/2176p_part_a.tar.gz',
            'http://download.opencontent.netflix.com.s3.amazonaws.com/bvi_aom_dataset/2176p_part_b.tar.gz',
            'http://download.opencontent.netflix.com.s3.amazonaws.com/bvi_aom_dataset/2176p_part_c.tar.gz',
            'http://download.opencontent.netflix.com.s3.amazonaws.com/bvi_aom_dataset/2176p_part_d.tar.gz',
            'http://download.opencontent.netflix.com.s3.amazonaws.com/bvi_aom_dataset/2176p_part_e.tar.gz',
            'http://download.opencontent.netflix.com.s3.amazonaws.com/bvi_aom_dataset/2176p_part_f.tar.gz'],
            '1920x1088': 'http://download.opencontent.netflix.com.s3.amazonaws.com/bvi_aom_dataset/1088p.tar.gz',
            '960x544': 'http://download.opencontent.netflix.com.s3.amazonaws.com/bvi_aom_dataset/544p.tar.gz',
            '480x272': 'http://download.opencontent.netflix.com.s3.amazonaws.com/bvi_aom_dataset/272p.tar.gz'
            }
        os.makedirs(self.storage_path, exist_ok=True)
        self.setup()
    
    def setup(self) -> None:
        if isinstance(self.resolutions, (list, tuple)):
            for _resolution in self.resolutions:
                self._download_and_unpack_tar(_resolution)
        else:
            self._download_and_unpack_tar(self.resolutions)
    
    def _download_and_unpack_tar(self, resolution: str) -> None:
        
        tar_link = self.cloud_links[resolution]
        local_tar_file = os.path.join(self.storage_path, os.path.basename(tar_link))
        
        if isinstance(tar_link, (list, tuple)):
            for _resolution in tar_link:
                self._download_file(tar_link, self.storage_path)
                self._unpack_tar(local_tar_file, self.storage_path)
        else:
            self._download_file(tar_link, self.storage_path)
            self._unpack_tar(local_tar_file, self.storage_path)

    def _download_file(self, url_link: str, save_dir: str) -> None:
        file_name = os.path.basename(url_link)
        if os.path.exists(os.path.join(save_dir, file_name)):
            print(f"File {os.path.join(self.storage_path, file_name)} already found, skipping download...")
        else:
            print(f"Downloading {file_name} to {save_dir}...")
            wget.download(url_link, save_dir)
    
    def _unpack_tar(self, tar_file: str, out_folder: str) -> None:
        try:
            print(f"\nExtracting {tar_file} to {out_folder}")
            with tarfile.open(tar_file, "r:gz") as tar:
                tar.extractall(path=out_folder)
            print(f"Extraction completed")
        except tarfile.ReadError:
            print(f"Error reading file: {tar_file}. It might be corrupted or not a valid tar file.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        if self.remove_tar:
            if os.path.exists(tar_file):
                os.remove(tar_file)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Download BVI-AOM dataset')
    parser.add_argument('storage_path', type=str, help='Path to store the dataset')
    parser.add_argument('--resolutions', '-r', nargs='+', 
                        choices=['3840x2176', '1920x1088', '960x544', '480x272'],
                        metavar='RES',
                        required=True,
                        help='Resolution(s) to download: 3840x2176, 1920x1088, 960x544, 480x272')
    parser.add_argument('--remove-tar', action='store_true',
                        help='Remove tar files after extraction')
    
    args = parser.parse_args()
    
    BVIAOMDataset(args.storage_path, args.resolutions, remove_tar=args.remove_tar)