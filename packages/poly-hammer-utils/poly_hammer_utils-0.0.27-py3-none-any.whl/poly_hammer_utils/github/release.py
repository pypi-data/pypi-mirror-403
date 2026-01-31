

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from github import Github, GitReleaseAsset
import requests

logger = logging.getLogger(__name__)

class GitHubRelease:
    def __init__(
            self, 
            github_token: str | None = None, 
            repo: str | None = None
        ):
        self._github_token = github_token or os.environ['GH_PAT']
        self.client = Github(login_or_token=self._github_token)
        self.repo = self.client.get_repo(repo or os.environ['GITHUB_REPO'])


    def get_previous_releases(self, include_prereleases: bool = False) -> list[str]:
        """
        Gets the previous releases.

        Args:
            include_prereleases (bool): Whether to include prerelease versions. Defaults to False.

        Returns:
            list[str]: A list of the previous addon releases.
        """
        return [
            release.tag_name 
            for release in self.repo.get_releases() 
            if include_prereleases or not release.prerelease
        ]
    
    def get_releases_attachments(self, tag: str) -> tuple[str, list[GitReleaseAsset.GitReleaseAsset]]:
        """
        Gets the release attachments. That match the tag.

        Args:
            tag (str): The tag to get the attachments for.

        Returns:
            tuple[str, list[GitReleaseAsset.GitReleaseAsset]]: The tag name and the attachments.
        """
        for release in self.repo.get_releases():
            if tag.lower() == 'latest':
                return release.tag_name, [asset for asset in release.get_assets()]

            if release.tag_name == tag:
                return release.tag_name, [asset for asset in release.get_assets()]
            
        return '', []
    

    def delete_release(self, tag_name: str):
        """
        Deletes a release.
        
        Args:
            tag_name (str): The tag name of the release to delete.
        """
        for release in self.repo.get_releases():
            if release.tag_name == tag_name:
                release.delete_release()
                logger.debug(f'Deleted release "{tag_name}"')

    def trigger_core_build_workflow(
            self, 
            repo: str,
            title: str,
            message: str,
            tag: str,
        ):
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._github_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        payload = {
            "event_type": "dispatch-event",
            "client_payload": {
                "title": title,
                "message": message,
                "tag": tag
            }
        }

        response = requests.post(
            f"https://api.github.com/repos/{repo}/dispatches",
            headers=headers,
            json=payload
        )

        if response.status_code == 204:
            logger.info("Successfully triggered the core build workflow.")
        else:
            raise RuntimeError(f"Failed to trigger the core build workflow: {response.status_code} {response.text}")
        

    def trigger_build_workflow(
            self, 
            repo: str, 
            event_type: str = "dispatch-event",
            await_completion: bool = False,
            poll_interval: int = 10,
            timeout: int = 1200
        ):
        """
        Triggers a build workflow via repository dispatch.

        Args:
            repo (str): The repository to trigger the workflow on (format: owner/repo).
            event_type (str): The event type for the dispatch. Defaults to "dispatch-event".
            await_completion (bool): Whether to poll until the workflow completes. Defaults to False.
            poll_interval (int): Seconds between status checks when awaiting. Defaults to 10.
            timeout (int): Maximum seconds to wait for completion. Defaults to 1200.

        Raises:
            RuntimeError: If the workflow fails to trigger or times out.
        """
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._github_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        payload = {
            "event_type": event_type,
            "client_payload": {}
        }

        # Record time before triggering to help identify our workflow run
        trigger_time = time.time()

        response = requests.post(
            f"https://api.github.com/repos/{repo}/dispatches",
            headers=headers,
            json=payload
        )

        if response.status_code == 204:
            logger.info("Successfully triggered the build workflow.")
        else:
            raise RuntimeError(f"Failed to trigger the build workflow: {response.status_code} {response.text}")

        if await_completion:
            self._await_workflow_completion(
                repo=repo,
                trigger_time=trigger_time,
                headers=headers,
                poll_interval=poll_interval,
                timeout=timeout
            )

    def _await_workflow_completion(
            self,
            repo: str,
            trigger_time: float,
            headers: dict,
            poll_interval: int,
            timeout: int
        ):
        """
        Polls for workflow completion after triggering.

        Args:
            repo (str): The repository (format: owner/repo).
            trigger_time (float): Unix timestamp when the workflow was triggered.
            headers (dict): Request headers with authorization.
            poll_interval (int): Seconds between status checks.
            timeout (int): Maximum seconds to wait.

        Raises:
            RuntimeError: If the workflow fails or times out.
        """
        logger.info("Awaiting workflow completion...")
        start_time = time.time()
        workflow_run_id = None

        # Wait a moment for the workflow to register
        time.sleep(2)

        while time.time() - start_time < timeout:
            # Find workflow runs triggered after our dispatch
            response = requests.get(
                f"https://api.github.com/repos/{repo}/actions/runs",
                headers=headers,
                params={"per_page": 10}
            )

            if response.status_code != 200:
                logger.warning(f"Failed to fetch workflow runs: {response.status_code}")
                time.sleep(poll_interval)
                continue

            runs = response.json().get("workflow_runs", [])

            for run in runs:
                # Find a run that started after we triggered
                run_created = run.get("created_at", "")
                if run_created and workflow_run_id is None:
                    run_time = datetime.fromisoformat(run_created.replace("Z", "+00:00")).timestamp()
                    if run_time >= trigger_time - 5:  # 5 second buffer
                        workflow_run_id = run["id"]
                        logger.info(f"Found workflow run: {workflow_run_id}")
                        break

                if run["id"] == workflow_run_id:
                    status = run.get("status")
                    conclusion = run.get("conclusion")

                    if status == "completed":
                        if conclusion == "success":
                            logger.info("Workflow completed successfully.")
                            return
                        else:
                            raise RuntimeError(f"Workflow failed with conclusion: {conclusion}")

                    logger.debug(f"Workflow status: {status}")
                    break

            time.sleep(poll_interval)

        raise RuntimeError(f"Workflow timed out after {timeout} seconds")

    def create_release(
            self,
            file_paths: list[Path],
            title: str,
            message: str,
            tag: str,
        ):
        previous_releases = self.get_previous_releases()
        if tag not in previous_releases:
            logger.info(f'Creating release "{title}"')
            release = self.repo.create_git_release(
                name=title,
                message=message,
                tag=tag
            )

            for file_path in file_paths:
                logger.info(f'Uploading "{file_path}"')
                release.upload_asset(
                    path=str(file_path),
                    name=file_path.name,
                    content_type='application/zip'
                )
        else:            
            release = self.repo.get_release(tag)
            # Remove the asset if it already exists
            for asset in release.get_assets():
                for file_path in file_paths:
                    if asset.name == file_path.name:
                        asset.delete_asset()
                        logger.info(f'Deleting existing attachment "{asset.name}" on release "{tag}"')

            for file_path in file_paths:
                logger.info(f'Uploading additional attachment "{file_path}" to release "{tag}"')
                release.upload_asset(
                    path=str(file_path),
                name=file_path.name,
                content_type='application/zip'
            )
        
        logger.info('Successfully released core!')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    if sys.argv[-1] == 'core':
        GitHubRelease().create_release(
            file_paths=[Path(p.strip()) for p in os.environ['GITHUB_RELEASE_FILES'].split(',') if p.strip()],
            title=os.environ['GITHUB_RELEASE_TITLE'],
            message=os.environ['GITHUB_RELEASE_MESSAGE'],
            tag=os.environ['GITHUB_RELEASE_TAG']
        )
    elif sys.argv[-1] == 'trigger-repo-build':
        GitHubRelease().trigger_build_workflow(repo=os.environ['GITHUB_TRIGGER_REPO_BUILD'])
    