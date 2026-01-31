# Local repository analyzer for direct GitHub URL analysis using PyDriller.

from __future__ import annotations

import os
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator

from pydriller import Repository
from pydriller.metrics.process.change_set import ChangeSet
from pydriller.metrics.process.code_churn import CodeChurn
from pydriller.metrics.process.commits_count import CommitsCount
from pydriller.metrics.process.contributors_count import ContributorsCount
from pydriller.metrics.process.contributors_experience import ContributorsExperience
from pydriller.metrics.process.history_complexity import HistoryComplexity
from pydriller.metrics.process.hunks_count import HunksCount
from pydriller.metrics.process.lines_count import LinesCount

from greenmining.gsf_patterns import get_pattern_by_keywords, is_green_aware, GSF_PATTERNS
from greenmining.utils import colored_print


@dataclass
class CommitAnalysis:
    # Analysis result for a single commit.
    
    hash: str
    message: str
    author: str
    author_email: str
    date: datetime
    green_aware: bool
    gsf_patterns_matched: List[str]
    pattern_count: int
    pattern_details: List[Dict[str, Any]]
    confidence: str
    files_modified: List[str]
    insertions: int
    deletions: int
    
    # PyDriller DMM metrics
    dmm_unit_size: Optional[float] = None
    dmm_unit_complexity: Optional[float] = None
    dmm_unit_interfacing: Optional[float] = None
    
    # Structural metrics (Lizard)
    total_nloc: int = 0
    total_complexity: int = 0
    max_complexity: int = 0
    methods_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        # Convert to dictionary.
        return {
            "commit_hash": self.hash,
            "message": self.message,
            "author": self.author,
            "author_email": self.author_email,
            "date": self.date.isoformat() if self.date else None,
            "green_aware": self.green_aware,
            "gsf_patterns_matched": self.gsf_patterns_matched,
            "pattern_count": self.pattern_count,
            "pattern_details": self.pattern_details,
            "confidence": self.confidence,
            "files_modified": self.files_modified,
            "insertions": self.insertions,
            "deletions": self.deletions,
            "dmm_unit_size": self.dmm_unit_size,
            "dmm_unit_complexity": self.dmm_unit_complexity,
            "dmm_unit_interfacing": self.dmm_unit_interfacing,
            "total_nloc": self.total_nloc,
            "total_complexity": self.total_complexity,
            "max_complexity": self.max_complexity,
            "methods_count": self.methods_count,
        }


@dataclass
class RepositoryAnalysis:
    # Complete analysis result for a repository.
    
    url: str
    name: str
    total_commits: int
    green_commits: int
    green_commit_rate: float
    commits: List[CommitAnalysis] = field(default_factory=list)
    process_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        # Convert to dictionary.
        return {
            "url": self.url,
            "name": self.name,
            "total_commits": self.total_commits,
            "green_commits": self.green_commits,
            "green_commit_rate": self.green_commit_rate,
            "commits": [c.to_dict() for c in self.commits],
            "process_metrics": self.process_metrics,
        }


class LocalRepoAnalyzer:
    # Analyze repositories directly from GitHub URLs using PyDriller.
    
    def __init__(
        self,
        clone_path: Optional[Path] = None,
        max_commits: int = 500,
        days_back: int = 730,
        skip_merges: bool = True,
        compute_process_metrics: bool = True,
        cleanup_after: bool = True,
    ):
        # Initialize the local repository analyzer.
        self.clone_path = clone_path or Path(tempfile.gettempdir()) / "greenmining_repos"
        self.clone_path.mkdir(parents=True, exist_ok=True)
        self.max_commits = max_commits
        self.days_back = days_back
        self.skip_merges = skip_merges
        self.compute_process_metrics = compute_process_metrics
        self.cleanup_after = cleanup_after
        self.gsf_patterns = GSF_PATTERNS
        
    def _parse_repo_url(self, url: str) -> tuple[str, str]:
        # Parse repository URL to extract owner and name.
        # Handle HTTPS URLs
        https_pattern = r"github\.com[/:]([^/]+)/([^/\.]+)"
        match = re.search(https_pattern, url)
        if match:
            return match.group(1), match.group(2).replace(".git", "")
        
        # Handle SSH URLs
        ssh_pattern = r"git@github\.com:([^/]+)/([^/\.]+)"
        match = re.search(ssh_pattern, url)
        if match:
            return match.group(1), match.group(2).replace(".git", "")
        
        raise ValueError(f"Could not parse GitHub URL: {url}")
    
    def _get_pattern_details(self, matched_patterns: List[str]) -> List[Dict[str, Any]]:
        # Get detailed pattern information.
        details = []
        for pattern_id, pattern in self.gsf_patterns.items():
            if pattern["name"] in matched_patterns:
                details.append({
                    "name": pattern["name"],
                    "category": pattern["category"],
                    "description": pattern["description"],
                    "sci_impact": pattern["sci_impact"],
                })
        return details
    
    def analyze_commit(self, commit) -> CommitAnalysis:
        # Analyze a single PyDriller commit object.
        message = commit.msg or ""
        
        # Green awareness check
        green_aware = is_green_aware(message)
        
        # GSF pattern matching
        matched_patterns = get_pattern_by_keywords(message)
        pattern_details = self._get_pattern_details(matched_patterns)
        
        # Confidence calculation
        pattern_count = len(matched_patterns)
        confidence = "high" if pattern_count >= 2 else "medium" if pattern_count == 1 else "low"
        
        # File modifications
        files_modified = [mod.filename for mod in commit.modified_files]
        insertions = sum(mod.added_lines for mod in commit.modified_files)
        deletions = sum(mod.deleted_lines for mod in commit.modified_files)
        
        # Delta Maintainability Model (if available)
        dmm_unit_size = None
        dmm_unit_complexity = None
        dmm_unit_interfacing = None
        
        try:
            dmm_unit_size = commit.dmm_unit_size
            dmm_unit_complexity = commit.dmm_unit_complexity
            dmm_unit_interfacing = commit.dmm_unit_interfacing
        except Exception:
            pass  # DMM may not be available for all commits
        
        # Structural metrics from Lizard (via PyDriller)
        total_nloc = 0
        total_complexity = 0
        max_complexity = 0
        methods_count = 0
        
        try:
            for mod in commit.modified_files:
                if mod.nloc:
                    total_nloc += mod.nloc
                if mod.complexity:
                    total_complexity += mod.complexity
                    if mod.complexity > max_complexity:
                        max_complexity = mod.complexity
                if mod.methods:
                    methods_count += len(mod.methods)
        except Exception:
            pass  # Structural metrics may fail for some files
        
        return CommitAnalysis(
            hash=commit.hash,
            message=message,
            author=commit.author.name,
            author_email=commit.author.email,
            date=commit.author_date,
            green_aware=green_aware,
            gsf_patterns_matched=matched_patterns,
            pattern_count=pattern_count,
            pattern_details=pattern_details,
            confidence=confidence,
            files_modified=files_modified,
            insertions=insertions,
            deletions=deletions,
            dmm_unit_size=dmm_unit_size,
            dmm_unit_complexity=dmm_unit_complexity,
            dmm_unit_interfacing=dmm_unit_interfacing,
            total_nloc=total_nloc,
            total_complexity=total_complexity,
            max_complexity=max_complexity,
            methods_count=methods_count,
        )
    
    def analyze_repository(self, url: str) -> RepositoryAnalysis:
        # Analyze a repository from its URL.
        owner, repo_name = self._parse_repo_url(url)
        full_name = f"{owner}/{repo_name}"
        
        colored_print(f"\n Analyzing repository: {full_name}", "cyan")
        
        # Calculate date range
        since_date = datetime.now() - timedelta(days=self.days_back)
        
        # Configure PyDriller Repository
        repo_config = {
            "path_to_repo": url,
            "since": since_date,
            "only_no_merge": self.skip_merges,
        }
        
        # Clone to specific path if needed
        local_path = self.clone_path / repo_name
        if local_path.exists():
            shutil.rmtree(local_path)
        
        repo_config["clone_repo_to"] = str(self.clone_path)
        
        colored_print(f"   Cloning to: {local_path}", "cyan")
        
        commits_analyzed = []
        commit_count = 0
        
        try:
            for commit in Repository(**repo_config).traverse_commits():
                if commit_count >= self.max_commits:
                    break
                
                try:
                    analysis = self.analyze_commit(commit)
                    commits_analyzed.append(analysis)
                    commit_count += 1
                    
                    if commit_count % 50 == 0:
                        colored_print(f"   Processed {commit_count} commits...", "cyan")
                        
                except Exception as e:
                    colored_print(f"   Warning: Error analyzing commit {commit.hash[:8]}: {e}", "yellow")
                    continue
            
            colored_print(f"    Analyzed {len(commits_analyzed)} commits", "green")
            
            # Compute process metrics if enabled
            process_metrics = {}
            if self.compute_process_metrics and local_path.exists():
                colored_print("   Computing process metrics...", "cyan")
                process_metrics = self._compute_process_metrics(str(local_path))
            
            # Calculate summary
            green_commits = sum(1 for c in commits_analyzed if c.green_aware)
            green_rate = green_commits / len(commits_analyzed) if commits_analyzed else 0
            
            result = RepositoryAnalysis(
                url=url,
                name=full_name,
                total_commits=len(commits_analyzed),
                green_commits=green_commits,
                green_commit_rate=green_rate,
                commits=commits_analyzed,
                process_metrics=process_metrics,
            )
            
            return result
            
        finally:
            # Cleanup if requested
            if self.cleanup_after and local_path.exists():
                colored_print(f"   Cleaning up: {local_path}", "cyan")
                shutil.rmtree(local_path, ignore_errors=True)
    
    def _compute_process_metrics(self, repo_path: str) -> Dict[str, Any]:
        # Compute PyDriller process metrics for the repository.
        metrics = {}
        since_date = datetime.now() - timedelta(days=self.days_back)
        to_date = datetime.now()
        
        try:
            # ChangeSet metrics
            cs = ChangeSet(repo_path, since=since_date, to=to_date)
            metrics["change_set_max"] = cs.max()
            metrics["change_set_avg"] = cs.avg()
        except Exception as e:
            colored_print(f"   Warning: ChangeSet metrics failed: {e}", "yellow")
        
        try:
            # CodeChurn metrics
            churn = CodeChurn(repo_path, since=since_date, to=to_date)
            metrics["code_churn"] = churn.count()
        except Exception as e:
            colored_print(f"   Warning: CodeChurn metrics failed: {e}", "yellow")
        
        try:
            # CommitsCount metrics
            cc = CommitsCount(repo_path, since=since_date, to=to_date)
            metrics["commits_per_file"] = cc.count()
        except Exception as e:
            colored_print(f"   Warning: CommitsCount metrics failed: {e}", "yellow")
        
        try:
            # ContributorsCount metrics
            contrib = ContributorsCount(repo_path, since=since_date, to=to_date)
            metrics["contributors_per_file"] = contrib.count()
        except Exception as e:
            colored_print(f"   Warning: ContributorsCount metrics failed: {e}", "yellow")
        
        try:
            # ContributorsExperience metrics
            exp = ContributorsExperience(repo_path, since=since_date, to=to_date)
            metrics["contributors_experience"] = exp.count()
        except Exception as e:
            colored_print(f"   Warning: ContributorsExperience metrics failed: {e}", "yellow")
        
        try:
            # HistoryComplexity metrics
            hc = HistoryComplexity(repo_path, since=since_date, to=to_date)
            metrics["history_complexity"] = hc.count()
        except Exception as e:
            colored_print(f"   Warning: HistoryComplexity metrics failed: {e}", "yellow")
        
        try:
            # HunksCount metrics
            hunks = HunksCount(repo_path, since=since_date, to=to_date)
            metrics["hunks_count"] = hunks.count()
        except Exception as e:
            colored_print(f"   Warning: HunksCount metrics failed: {e}", "yellow")
        
        try:
            # LinesCount metrics
            lines = LinesCount(repo_path, since=since_date, to=to_date)
            metrics["lines_count"] = lines.count()
        except Exception as e:
            colored_print(f"   Warning: LinesCount metrics failed: {e}", "yellow")
        
        return metrics
    
    def analyze_repositories(self, urls: List[str]) -> List[RepositoryAnalysis]:
        # Analyze multiple repositories from URLs.
        results = []
        
        for i, url in enumerate(urls, 1):
            colored_print(f"\n[{i}/{len(urls)}] Processing repository...", "cyan")
            try:
                result = self.analyze_repository(url)
                results.append(result)
            except Exception as e:
                colored_print(f"   Error analyzing {url}: {e}", "red")
                continue
        
        return results
