from typing import Union
import os 
import tarfile

import requests
from tqdm import tqdm

class BVIAOMDataset:
    def __init__(self, storage_path: str, resolutions: Union[tuple[str], list[str], str], remove_tar: bool = False,
                 timeout: int = 300, max_retries: int = 10):
        """
        Initialize the BVI-AOM Dataset downloader.
        
        Args:
            storage_path: Path to store the downloaded files
            resolutions: Resolution(s) to download
            remove_tar: Whether to remove tar files after extraction
            timeout: Timeout in seconds for wget (detects stalls). Default 300s (5 min).
            max_retries: Maximum number of retry attempts for stalled downloads. Default 10.
        """
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
        self.timeout = timeout
        self.max_retries = max_retries
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
        """
        Download a file using requests with resume support.
        
        Uses HTTP Range headers to continue partial downloads if they exist.
        If the download stalls or fails, it will automatically retry up to 
        max_retries times, continuing from where it left off.
        """
        file_name = os.path.basename(url_link)
        file_path = os.path.join(save_dir, file_name)
        
        attempt = 0
        while attempt < self.max_retries:
            try:
                # Get current file size for resume
                resume_pos = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                
                # Set Range header for resume
                headers = {'Range': f'bytes={resume_pos}-'} if resume_pos else {}
                
                if resume_pos:
                    print(f"Resuming {file_name} from {resume_pos / (1024**3):.2f} GB...")
                else:
                    print(f"Downloading {file_name} to {save_dir}...")
                
                # timeout=(connect_timeout, read_timeout)
                # - connect: time to establish connection (10s is usually enough)
                # - read: time to wait for data chunks (detects stalls)
                with requests.get(url_link, headers=headers, stream=True, timeout=(10, self.timeout)) as r:
                    r.raise_for_status()
                    
                    # Get total size from Content-Length or Content-Range
                    if resume_pos and 'Content-Range' in r.headers:
                        # Content-Range format: "bytes start-end/total"
                        total_size = int(r.headers['Content-Range'].split('/')[-1])
                    else:
                        total_size = int(r.headers.get('content-length', 0)) + resume_pos
                    
                    # Check if already complete (server returns 416 Range Not Satisfiable or 0 content-length)
                    if r.status_code == 416 or (resume_pos > 0 and int(r.headers.get('content-length', 1)) == 0):
                        print(f"Download already complete: {file_name}")
                        return
                    
                    mode = 'ab' if resume_pos else 'wb'
                    
                    with open(file_path, mode) as f, tqdm(
                        total=total_size,
                        initial=resume_pos,
                        unit='B',
                        unit_scale=True,
                        unit_divisor=1024,
                        desc=file_name
                    ) as pbar:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:  # Filter out keep-alive chunks
                                f.write(chunk)
                                pbar.update(len(chunk))
                
                print(f"Download completed: {file_name}")
                return  # Success, exit the retry loop
                
            except requests.exceptions.Timeout:
                attempt += 1
                if attempt < self.max_retries:
                    print(f"\nDownload stalled - no data received for {self.timeout}s (attempt {attempt}/{self.max_retries})")
                    print("Retrying and continuing from where we left off...")
                else:
                    print(f"\nDownload failed after {self.max_retries} attempts due to repeated stalls.")
                    raise RuntimeError(f"Failed to download {file_name} after {self.max_retries} attempts - connection keeps stalling")
            except (requests.exceptions.RequestException, IOError) as e:
                attempt += 1
                if attempt < self.max_retries:
                    print(f"\nDownload failed (attempt {attempt}/{self.max_retries}): {e}")
                    print("Retrying and continuing from where we left off...")
                else:
                    print(f"\nDownload failed after {self.max_retries} attempts.")
                    raise RuntimeError(f"Failed to download {file_name} after {self.max_retries} attempts") from e
    
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
    parser.add_argument('--timeout', '-t', type=int, default=300,
                        help='Timeout in seconds for detecting stalled downloads (default: 300)')
    parser.add_argument('--max-retries', '-m', type=int, default=10,
                        help='Maximum retry attempts for stalled downloads (default: 10)')
    
    args = parser.parse_args()
    
    BVIAOMDataset(args.storage_path, args.resolutions, remove_tar=args.remove_tar,
                  timeout=args.timeout, max_retries=args.max_retries)