#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GTAXOPROP - A utility to generate input files for taxonomy propagation and assignment in QIIME/QIIME2 from the NCBI database
Converts NCBI accession numbers to QIIME/QIIME2-compatible taxonomy files.
Supports both FASTA files and accession lists with API fallback.

Copyright (C) 2025  Maulana Malik Nashrulloh, Sonia Az Zahra Defi, 
                    Brian Rahardi, Muhammad Badrut Tamam, 
                    Riki Ruhimat, Hessy Novita

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

---------------------------------------------------------------------
ORIGINAL WORK ACKNOWLEDGMENT:

This program is a derivative work based on "entrez_qiime" v2.0
Original source: https://github.com/bakerccm/entrez_qiime
Original author: Chris Baker (ccmbaker@fas.harvard.edu)
Original copyright: (C) 2016 Chris Baker
Original license: GNU General Public License v3 (GPLv3)

This derivative work maintains the same GPLv3 license.
Substantial modifications have been made including:
- Complete Python 3 migration
- Integration of cogent3 library
- Enhanced caching system
- Batch API processing
- Resume functionality
---------------------------------------------------------------------

Current maintainer: Maulana Malik Nashrulloh (maulana@genbinesia.or.id)
Contributors: Sonia Az Zahra Defi, Brian Rahardi, Muhammad Badrut Tamam, 
              Riki Ruhimat, Hessy Novita

Last modified: 20 August 2025
Version: 1.0.post3
"""

import argparse
import os
import sys
import time
import tempfile
import pickle
import hashlib
from collections import defaultdict
from textwrap import dedent
from time import localtime, strftime

try:
    from cogent3 import load_tree, make_tree
    from cogent3.core.tree import *
    COGENT3_AVAILABLE = True
except ImportError:
    COGENT3_AVAILABLE = False
    print("Error: cogent3 is required. Install with: pip install cogent3")
    sys.exit(1)

try:
    from Bio import Entrez
    from Bio import SeqIO
    BIOPYTHON_AVAILABLE = True
except ImportError:
    BIOPYTHON_AVAILABLE = False
    print("Error: biopython is required. Install with: pip install biopython")
    sys.exit(1)


class NcbiTaxonNode:
    """NCBI taxonomy node representation."""
    
    def __init__(self, taxid, parent_taxid, rank, name):
        self.TaxonId = taxid
        self.ParentId = parent_taxid
        self.Rank = rank
        self.Name = name
        self.Parent = None
        self.Children = []
    
    def __repr__(self):
        return f"NcbiTaxonNode(TaxonId={self.TaxonId}, Name={self.Name}, Rank={self.Rank})"


class NcbiTaxonomy:
    """NCBI taxonomy database handler."""
    
    def __init__(self):
        self.nodes = {}
        self.names = {}
    
    def __getitem__(self, taxid):
        return self.nodes.get(str(taxid))
    
    def get(self, taxid, default=None):
        return self.nodes.get(str(taxid), default)


class TaxonomyCache:
    """Cache for taxonomy mapping results to enable resuming interrupted processes."""
    
    def __init__(self, cache_dir=None):
        if cache_dir is None:
            cache_dir = tempfile.gettempdir()
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_cache_key(self, accessions, taxonomy_files, output_ranks):
        """Generate a unique cache key based on input parameters."""
        key_data = {
            'accessions': sorted(accessions),
            'taxonomy_files': {k: os.path.getmtime(v) for k, v in taxonomy_files.items() 
                              if os.path.exists(v)},
            'output_ranks': output_ranks
        }
        key_string = str(key_data).encode('utf-8')
        return hashlib.md5(key_string).hexdigest()
    
    def get_cache_file(self, cache_key):
        """Get cache file path for given key."""
        return os.path.join(self.cache_dir, f"taxonomy_cache_{cache_key}.pkl")
    
    def save_progress(self, cache_key, progress_data):
        """Save progress data to cache."""
        cache_file = self.get_cache_file(cache_key)
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(progress_data, f)
            return True
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")
            return False
    
    def load_progress(self, cache_key):
        """Load progress data from cache."""
        cache_file = self.get_cache_file(cache_key)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Warning: Could not load cache: {e}")
        return None
    
    def cleanup_old_cache(self, max_age_hours=24):
        """Clean up cache files older than specified hours."""
        try:
            current_time = time.time()
            for filename in os.listdir(self.cache_dir):
                if filename.startswith("taxonomy_cache_") and filename.endswith(".pkl"):
                    filepath = os.path.join(self.cache_dir, filename)
                    file_age = current_time - os.path.getmtime(filepath)
                    if file_age > max_age_hours * 3600:
                        os.remove(filepath)
                        print(f"Cleaned up old cache file: {filename}")
        except Exception as e:
            print(f"Warning: Could not clean up cache: {e}")


class TaxonomyProcessor:
    """Main taxonomy processing class."""
    
    def __init__(self, args):
        self.args = args
        self.setup_logging()
        
        # Initialize cache
        cache_dir = getattr(args, 'cache_dir', None)
        self.cache = TaxonomyCache(cache_dir)
        
        # Set NCBI email for API access
        if hasattr(args, 'ncbi_email'):
            Entrez.email = args.ncbi_email
        else:
            Entrez.email = "unknown@example.com"
        Entrez.tool = "TaxonomyProcessor/1.0"
        
    def setup_logging(self):
        """Initialize logging system."""
        self.log_messages = []
        
    def log(self, message, error=False):
        """Log message with timestamp."""
        timestamp = strftime("%H:%M:%S", localtime())
        prefix = "ERROR: " if error else "INFO:  "
        formatted_message = f"{timestamp} {prefix}{message}"
        
        self.log_messages.append(formatted_message)
        
        if error or self.args.debug_mode:
            print(formatted_message, file=sys.stderr if error else sys.stdout)
            
        # Write to log file if available
        if hasattr(self.args, 'logfile_path'):
            try:
                with open(self.args.logfile_path, 'a', encoding='utf-8') as f:
                    f.write(formatted_message + '\n')
            except Exception:
                pass

    def validate_arguments(self):
        """Validate command line arguments."""
        if not COGENT3_AVAILABLE:
            raise RuntimeError("cogent3 is required but not installed")
        if not BIOPYTHON_AVAILABLE:
            raise RuntimeError("biopython is required but not installed")
        
        valid_ranks = {
            'acellular_root', 'cellular_root', 'class', 'domain', 'family', 'forma', 'genus', 'infraclass', 
            'infraorder', 'kingdom', 'no_rank', 'order', 'parvorder', 
            'phylum', 'species', 'realm', 'species_group', 'species_subgroup', 
            'subclass', 'subfamily', 'subgenus', 'subkingdom', 'suborder', 
            'subphylum', 'subspecies', 'subtribe', 'superclass', 'superfamily', 
            'superkingdom', 'superorder', 'superphylum', 'tribe', 'varietas'
        }
        
        input_ranks = {rank.replace('_', ' ') for rank in self.args.output_ranks.split(',')}
        invalid_ranks = input_ranks - valid_ranks
        
        if invalid_ranks:
            raise ValueError(f"Invalid ranks: {', '.join(invalid_ranks)}")

    def detect_encoding(self, filepath):
        """Detect file encoding."""
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'windows-1252']
        
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    f.read(1024)
                self.log(f"Detected encoding: {encoding} for {filepath}")
                return encoding
            except UnicodeDecodeError:
                continue
        
        # Fallback with error handling
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                f.read(1024)
            self.log(f"Using UTF-8 with error replacement for {filepath}")
            return 'utf-8'
        except Exception:
            self.log(f"Warning: Using UTF-8 for {filepath}", error=True)
            return 'utf-8'

    def setup_output_files(self):
        """Configure output file paths."""
        if self.args.infile_fasta_path:
            input_dir = os.path.dirname(self.args.infile_fasta_path)
            input_name = os.path.splitext(os.path.basename(self.args.infile_fasta_path))[0].rstrip(".")
        else:
            input_dir = os.path.dirname(self.args.infile_list_path)
            input_name = os.path.splitext(os.path.basename(self.args.infile_list_path))[0].rstrip(".")
        
        timestamp = strftime("%Y%m%d%H%M%S", localtime())
        
        # Output file
        if not self.args.outfile_path:
            outfile = os.path.join(input_dir, f"{input_name}_accession_taxonomy.txt")
        elif os.path.isdir(self.args.outfile_path):
            outfile = os.path.join(self.args.outfile_path, f"{input_name}_accession_taxonomy.txt")
        else:
            outfile = self.args.outfile_path
        
        # Log file
        if not self.args.logfile_path:
            logfile = os.path.join(input_dir, f"{input_name}.log")
        elif os.path.isdir(self.args.logfile_path):
            logfile = os.path.join(self.args.logfile_path, f"{input_name}.log")
        else:
            logfile = self.args.logfile_path
        
        # Handle existing files
        outfile = os.path.abspath(outfile)
        logfile = os.path.abspath(logfile)
        
        os.makedirs(os.path.dirname(outfile), exist_ok=True)
        os.makedirs(os.path.dirname(logfile), exist_ok=True)
        
        if not self.args.force_overwrite:
            for filepath in [outfile, logfile]:
                if os.path.exists(filepath):
                    base, ext = os.path.splitext(filepath)
                    new_path = f"{base}_{timestamp}{ext}"
                    os.rename(filepath, new_path)
                    self.log(f"Renamed existing file: {filepath} -> {new_path}")
        
        # Initialize log file
        self.args.logfile_path = logfile
        with open(logfile, 'w', encoding='utf-8') as f:
            f.write(f'Log file created at {self.current_timestamp()}\n')
            f.write('Using GTAXOPTROP v.1.0.post1 (Python 3 + cogent3 + biopython)\n')
        
        return outfile, logfile

    def current_timestamp(self):
        """Get formatted timestamp."""
        return strftime("%H:%M:%S on %d-%m-%Y", localtime())

    def load_taxonomy_files(self):
        """Load NCBI taxonomy database files."""
        taxonomy_dir = self.args.ncbi_taxonomy_dir
        
        required_files = {
            'nodes.dmp': None,
            'names.dmp': None, 
            'merged.dmp': None,
            'delnodes.dmp': None
        }
        
        for filename in required_files:
            filepath = os.path.join(taxonomy_dir, filename)
            if not os.path.isfile(filepath):
                raise FileNotFoundError(f"Missing taxonomy file: {filepath}")
            required_files[filename] = filepath
            self.log(f"Found taxonomy file: {filepath}")
        
        return required_files

    def parse_taxonomy_files(self, nodes_path, names_path):
        """Parse NCBI taxonomy files into taxonomy object."""
        nodes_encoding = self.detect_encoding(nodes_path)
        names_encoding = self.detect_encoding(names_path)
        
        with open(nodes_path, 'r', encoding=nodes_encoding) as nodes_file, \
             open(names_path, 'r', encoding=names_encoding) as names_file:
            
            taxonomy = NcbiTaxonomy()
            
            # Parse nodes.dmp
            for line in nodes_file:
                if not line.strip():
                    continue
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 3:
                    taxid, parent_taxid, rank = parts[0], parts[1], parts[2]
                    taxonomy.nodes[taxid] = NcbiTaxonNode(taxid, parent_taxid, rank, "")
            
            # Build parent-child relationships
            for taxid, node in taxonomy.nodes.items():
                if node.ParentId in taxonomy.nodes:
                    node.Parent = taxonomy.nodes[node.ParentId]
                    taxonomy.nodes[node.ParentId].Children.append(node)
                elif node.ParentId != '1':
                    self.log(f"Warning: Parent {node.ParentId} not found for {taxid}")
            
            # Parse names.dmp
            for line in names_file:
                if not line.strip():
                    continue
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 4:
                    taxid, name, name_type = parts[0], parts[1], parts[3]
                    if name_type == "scientific name" and taxid in taxonomy.nodes:
                        taxonomy.nodes[taxid].Name = name
                    taxonomy.names[taxid] = name
            
            self.log(f"Loaded taxonomy with {len(taxonomy.nodes)} nodes")
            return taxonomy

    def get_accessions_from_input(self):
        """Extract accession numbers from input file."""
        accessions = set()
        max_accessions = 1000000  # Safety limit
        
        if self.args.infile_fasta_path:
            filepath = self.args.infile_fasta_path
            encoding = self.detect_encoding(filepath)
            
            with open(filepath, 'r', encoding=encoding) as f:
                for line_num, line in enumerate(f, 1):
                    if line.startswith('>'):
                        # More robust accession extraction
                        header = line[1:].strip()
                        accession = header.split()[0]  # First word is usually accession
                        if accession and len(accessions) < max_accessions:
                            accessions.add(accession)
                    
                    if line_num % 100000 == 0:
                        self.log(f"Processed {line_num} lines, {len(accessions)} accessions")
        else:
            filepath = self.args.infile_list_path
            encoding = self.detect_encoding(filepath)
            
            with open(filepath, 'r', encoding=encoding) as f:
                for line_num, line in enumerate(f, 1):
                    accession = line.strip()
                    if accession and len(accessions) < max_accessions:
                        accessions.add(accession)
                    
                    if line_num % 100000 == 0:
                        self.log(f"Processed {line_num} lines, {len(accessions)} accessions")
        
        if len(accessions) >= max_accessions:
            self.log(f"Limited to {max_accessions} accessions for memory safety")
        
        self.log(f"Found {len(accessions)} unique accessions in input")
        return list(accessions)  # Return as list for consistent ordering

    def fetch_taxids_batch(self, accessions, batch_size=50, progress_data=None):
        """Fetch taxids for multiple accessions in batches using Biopython."""
        taxid_map = progress_data.get('taxid_map', {}) if progress_data else {}
        total_batches = (len(accessions) + batch_size - 1) // batch_size
        
        # Filter out already processed accessions
        unprocessed_accessions = [acc for acc in accessions if acc not in taxid_map]
        
        self.log(f"Resuming from cache: {len(taxid_map)} already processed, {len(unprocessed_accessions)} remaining")
        
        for batch_num, i in enumerate(range(0, len(unprocessed_accessions), batch_size), 1):
            batch = unprocessed_accessions[i:i + batch_size]
            self.log(f"Processing batch {batch_num}/{total_batches} ({len(batch)} accessions)")
            
            try:
                # Fetch records in GenBank format
                handle = Entrez.efetch(
                    db="nuccore",
                    id=batch,
                    rettype="gb",
                    retmode="text"
                )
                
                # Parse using SeqIO
                records = list(SeqIO.parse(handle, "genbank"))
                handle.close()
                
                batch_found = 0
                for record in records:
                    accession = record.id
                    taxid = None
                    
                    # Look for db_xref in features (more reliable than summary)
                    for feature in record.features:
                        if 'db_xref' in feature.qualifiers:
                            for db_xref in feature.qualifiers['db_xref']:
                                if db_xref.startswith('taxon:'):
                                    taxid = db_xref.split(':')[1]
                                    break
                        if taxid:
                            break
                    
                    if taxid:
                        taxid_map[accession] = taxid
                        batch_found += 1
                    else:
                        self.log(f"No taxon ID found for accession: {accession}")
                        taxid_map[accession] = None
                
                # Handle accessions that returned no records
                found_accessions = {record.id for record in records}
                for accession in batch:
                    if accession not in found_accessions:
                        self.log(f"No record found for accession: {accession}")
                        taxid_map[accession] = None
                
                self.log(f"Batch {batch_num}: {batch_found}/{len(batch)} taxids found")
                
                # Save progress after each batch
                if progress_data:
                    progress_data['taxid_map'] = taxid_map
                    cache_key = progress_data.get('cache_key')
                    if cache_key:
                        self.cache.save_progress(cache_key, progress_data)
                        self.log("Progress saved to cache")
                
                # Respect API rate limiting
                time.sleep(self.args.api_delay)
                
            except Exception as e:
                self.log(f"Batch API error: {e}", error=True)
                # Mark all accessions in this batch as failed
                for accession in batch:
                    taxid_map[accession] = None
                
                # Save progress even on error
                if progress_data:
                    progress_data['taxid_map'] = taxid_map
                    cache_key = progress_data.get('cache_key')
                    if cache_key:
                        self.cache.save_progress(cache_key, progress_data)
                
                # Longer delay on error
                time.sleep(self.args.api_delay * 2)
        
        return taxid_map

    def process_accessions(self, accessions, taxonomy, merged_taxids, deleted_taxids, progress_data=None):
        """Main accession processing pipeline with batch API support and resume capability."""
        taxid_map = progress_data.get('taxid_map', {}) if progress_data else {}
        missing_accessions = set(accessions) - set(taxid_map.keys())
        processed_taxids = progress_data.get('processed_taxids', set()) if progress_data else set()
        included_nodes = progress_data.get('included_nodes', []) if progress_data else []
        
        self.log(f"Resuming processing: {len(taxid_map)} already mapped, {len(missing_accessions)} remaining")
        
        # Phase 1: Local accession2taxid file (only for missing accessions)
        if (missing_accessions and 
            hasattr(self.args, 'infile_acc2taxid_path') and 
            os.path.isfile(self.args.infile_acc2taxid_path) and
            os.path.getsize(self.args.infile_acc2taxid_path) > 0):
            
            self.log("Phase 1: Searching local accession2taxid file for missing accessions...")
            local_map = self.search_local_accession2taxid(
                list(missing_accessions), taxonomy, merged_taxids, deleted_taxids
            )
            taxid_map.update(local_map)
            missing_accessions = missing_accessions - set(local_map.keys())
            self.log(f"Phase 1 complete: {len(local_map)} additional accessions mapped locally")
            
            # Update progress
            if progress_data:
                progress_data['taxid_map'] = taxid_map
                cache_key = progress_data.get('cache_key')
                if cache_key:
                    self.cache.save_progress(cache_key, progress_data)
        
        # Phase 2: Batch API fallback
        if missing_accessions and not self.args.no_api:
            self.log(f"Phase 2: Batch API processing for {len(missing_accessions)} accessions...")
            
            # Convert to list for consistent ordering
            missing_list = list(missing_accessions)
            batch_map = self.fetch_taxids_batch(missing_list, progress_data=progress_data)
            
            # Process results and handle merged/deleted taxids
            api_mapped = 0
            for accession, taxid in batch_map.items():
                if taxid and accession in missing_accessions:  # Only process newly mapped
                    # Handle merged/deleted taxids
                    if taxid in merged_taxids:
                        new_taxid = merged_taxids[taxid]
                        self.log(f"TaxID {taxid} merged to {new_taxid} for {accession}")
                        taxid = new_taxid
                    if taxid in deleted_taxids:
                        self.log(f"TaxID {taxid} is deleted, using root for {accession}")
                        taxid = '1'
                    
                    taxid_map[accession] = taxid
                    api_mapped += 1
            
            self.log(f"Phase 2 complete: {api_mapped}/{len(missing_accessions)} accessions mapped via API")
        
        # Collect unique taxonomy nodes (only new ones)
        unique_taxids = set(taxid_map.values()) - {None} - processed_taxids
        for taxid in unique_taxids:
            if taxid not in processed_taxids:
                node = taxonomy.get(taxid)
                if node:
                    included_nodes.append(node)
                    processed_taxids.add(taxid)
        
        missing_accessions = set(accessions) - set(taxid_map.keys())
        self.log(f"Processing complete: {len(taxid_map)} mapped, {len(missing_accessions)} missing")
        
        # Update final progress data
        if progress_data:
            progress_data.update({
                'taxid_map': taxid_map,
                'processed_taxids': processed_taxids,
                'included_nodes': included_nodes,
                'completed': True
            })
        
        return included_nodes, taxid_map, missing_accessions

    def search_local_accession2taxid(self, accessions, taxonomy, merged_taxids, deleted_taxids):
        """Search local accession to taxid mapping file with improved performance."""
        taxid_map = {}
        
        # Create mapping for versionless accessions
        accessions_no_version = {acc.split('.')[0]: acc for acc in accessions}
        accessions_lookup = set(accessions_no_version.keys())
        
        try:
            encoding = self.detect_encoding(self.args.infile_acc2taxid_path)
            mapped_count = 0
            
            with open(self.args.infile_acc2taxid_path, 'r', encoding=encoding) as f:
                header = next(f)  # Skip header
                
                for line_num, line in enumerate(f, 2):
                    if not line.strip():
                        continue
                    
                    parts = line.rstrip().split('\t')
                    if len(parts) < 3:
                        continue
                    
                    acc_version = parts[1]
                    acc_no_ver = acc_version.split('.')[0]
                    
                    if acc_no_ver in accessions_lookup:
                        full_acc = accessions_no_version[acc_no_ver]
                        taxid = parts[2]
                        
                        # Handle merged/deleted taxids
                        if taxid in merged_taxids:
                            new_taxid = merged_taxids[taxid]
                            self.log(f"Local file: TaxID {taxid} merged to {new_taxid} for {full_acc}")
                            taxid = new_taxid
                        if taxid in deleted_taxids:
                            self.log(f"Local file: TaxID {taxid} is deleted, using root for {full_acc}")
                            taxid = '1'
                        
                        taxid_map[full_acc] = taxid
                        mapped_count += 1
                        
                        # Remove from lookup to avoid duplicate processing
                        accessions_lookup.discard(acc_no_ver)
                    
                    # Progress reporting
                    if line_num % 1000000 == 0:
                        self.log(f"Processed {line_num} lines from accession2taxid, {mapped_count} mapped")
            
            self.log(f"Local search mapped {mapped_count} accessions")
            
        except Exception as e:
            self.log(f"Error reading accession2taxid file: {e}", error=True)
        
        return taxid_map

    def generate_taxonomy_strings(self, nodes, taxonomy, output_ranks):
        """Generate taxonomy strings for taxids with improved lineage building."""
        taxid_taxonomy = {}
        ranks_lookup = {rank: idx for idx, rank in enumerate(output_ranks)}
        
        for node in nodes:
            lineage = ['NA'] * len(output_ranks)
            
            if node.TaxonId == '1':  # Root node
                lineage[0] = 'root'
                taxid_taxonomy[node.TaxonId] = lineage
                continue
            
            # Build lineage by traversing up the tree
            current = node
            lineage_data = {}
            visited = set()
            
            while current and current.TaxonId not in visited:
                visited.add(current.TaxonId)
                
                # Only include ranks that are in our output list
                if current.Rank in ranks_lookup:
                    lineage_data[current.Rank] = current.Name
                
                # Stop at root or if no parent
                if current.TaxonId == '1' or current.Parent is None:
                    break
                
                current = current.Parent
            
            # Fill output lineage in correct order
            for rank, name in lineage_data.items():
                lineage[ranks_lookup[rank]] = name
            
            taxid_taxonomy[node.TaxonId] = lineage
        
        missing_taxonomy = ['unknown'] + ['NA'] * (len(output_ranks) - 1)
        self.log(f"Generated taxonomy for {len(taxid_taxonomy)} taxids")
        
        return taxid_taxonomy, missing_taxonomy

    def write_output_file(self, outfile_path, taxid_taxonomy, taxid_map, missing_accessions, missing_taxonomy):
        """Write final output file with improved formatting."""
        output_ranks = [rank.replace('_', ' ') for rank in self.args.output_ranks.split(',')]
        
        with open(outfile_path, 'w', encoding='utf-8') as f:
            # Write comprehensive header
            f.write(f"# QIIME-compatible taxonomy file generated by NCBI Taxonomy to QIIME Converter\n")
            f.write(f"# Generated: {self.current_timestamp()}\n")
            f.write(f"# Taxonomy ranks: {';'.join(output_ranks)}\n")
            f.write(f"# Total accessions: {len(taxid_map) + len(missing_accessions)}\n")
            f.write(f"# Successfully mapped: {len(taxid_map)}\n")
            f.write(f"# Missing taxonomies: {len(missing_accessions)}\n")
            f.write(f"# Missing taxa are labeled as: {missing_taxonomy[0]}\n\n")
            
            # Write mapped accessions
            for accession, taxid in taxid_map.items():
                taxonomy = taxid_taxonomy.get(taxid, missing_taxonomy)
                f.write(f"{accession}\t{';'.join(taxonomy)}\n")
            
            # Write missing accessions
            for accession in missing_accessions:
                f.write(f"{accession}\t{';'.join(missing_taxonomy)}\n")
        
        self.log(f"Output file created: {outfile_path}")

    def run(self):
        """Main execution method with resume capability."""
        try:
            self.log(f"Starting taxonomy processing at {self.current_timestamp()}")
            
            # Validate and setup
            self.validate_arguments()
            taxonomy_files = self.load_taxonomy_files()
            self.args.outfile_path, self.args.logfile_path = self.setup_output_files()
            
            # Parse ranks
            output_ranks = [rank.replace('_', ' ') for rank in self.args.output_ranks.split(',')]
            self.log(f"Using taxonomic ranks: {', '.join(output_ranks)}")
            
            # Load data
            accessions = self.get_accessions_from_input()
            taxonomy = self.parse_taxonomy_files(taxonomy_files['nodes.dmp'], taxonomy_files['names.dmp'])
            
            # Load merged and deleted nodes
            merged_taxids = self.load_merged_nodes(taxonomy_files['merged.dmp'])
            deleted_taxids = self.load_deleted_nodes(taxonomy_files['delnodes.dmp'])
            
            # Check for cached progress
            cache_key = self.cache.get_cache_key(accessions, taxonomy_files, output_ranks)
            progress_data = self.cache.load_progress(cache_key)
            
            if progress_data and progress_data.get('completed'):
                self.log("Found completed cache, using cached results")
                included_nodes = progress_data.get('included_nodes', [])
                taxid_map = progress_data.get('taxid_map', {})
                missing_accessions = set(accessions) - set(taxid_map.keys())
            else:
                if progress_data:
                    self.log("Resuming from interrupted process")
                    progress_data['cache_key'] = cache_key
                else:
                    self.log("Starting new process")
                    progress_data = {
                        'cache_key': cache_key,
                        'taxid_map': {},
                        'processed_taxids': set(),
                        'included_nodes': [],
                        'completed': False
                    }
                
                # Process accessions with resume capability
                included_nodes, taxid_map, missing_accessions = self.process_accessions(
                    accessions, taxonomy, merged_taxids, deleted_taxids, progress_data
                )
                
                # Mark as completed and save final cache
                progress_data['completed'] = True
                self.cache.save_progress(cache_key, progress_data)
                self.log("Process completed and cache saved")
            
            # Generate taxonomy
            taxid_taxonomy, missing_taxonomy = self.generate_taxonomy_strings(
                included_nodes, taxonomy, output_ranks
            )
            
            # Write output
            self.write_output_file(
                self.args.outfile_path, taxid_taxonomy, taxid_map, 
                missing_accessions, missing_taxonomy
            )
            
            # Clean up cache
            self.cache.cleanup_old_cache()
            
            # Final summary
            success_rate = (len(taxid_map) / len(accessions)) * 100
            self.log(f"Completed successfully at {self.current_timestamp()}")
            self.log(f"Final results: {len(taxid_map)}/{len(accessions)} accessions mapped ({success_rate:.1f}%)")
            
        except Exception as e:
            self.log(f"Fatal error: {e}", error=True)
            import traceback
            self.log(f"Traceback: {traceback.format_exc()}", error=True)
            sys.exit(1)

    def load_merged_nodes(self, merged_path):
        """Load merged taxid mappings."""
        merged = {}
        try:
            encoding = self.detect_encoding(merged_path)
            with open(merged_path, 'r', encoding=encoding) as f:
                for line in f:
                    if line.strip():
                        parts = [part.strip() for part in line.split('|')]
                        if len(parts) >= 2:
                            merged[parts[0]] = parts[1]
            self.log(f"Loaded {len(merged)} merged taxids")
        except Exception as e:
            self.log(f"Error reading merged nodes: {e}", error=True)
        return merged

    def load_deleted_nodes(self, deleted_path):
        """Load deleted taxids."""
        deleted = set()
        try:
            encoding = self.detect_encoding(deleted_path)
            with open(deleted_path, 'r', encoding=encoding) as f:
                for line in f:
                    if line.strip():
                        taxid = line.split('|')[0].strip()
                        if taxid:
                            deleted.add(taxid)
            self.log(f"Loaded {len(deleted)} deleted taxids")
        except Exception as e:
            self.log(f"Error reading deleted nodes: {e}", error=True)
        return deleted


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate QIIME-compatible files from NCBI accessions and taxonomy',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent('''
            We support 48 NCBI taxonomic rank types (See: https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/data-reports/taxonomy/):
                no_rank, acellular_root, cellular_root, 
                domain, realm, 
                kingdom, subkingdom,
                superphylum, phylum, subphylum, 
                clade,
                superclass, class, subclass, infraclass,
                cohort, subcohort,
                superorder, order, suborder, infraorder, parvorder,
                superfamily, family, subfamily,
                tribe, subtribe,
                genus, subgenus,
                species_group, species_subgroup, species, subspecies,
                forma,                  
                varietas,
                strain,
                section, subsection,
                subvariety,
                genotype, 
                serotype,
                isolate,
                morph,
                series,
                forma_specialis,
                serogroup,
                biotype
            
            Please underscore(s) in rank names on command line such as 'cellular_root' instead of 'cellular root'.
            
            Note: 
                1. superkingdom rank had been replaced by domain rank (See: https://ncbiinsights.ncbi.nlm.nih.gov/2025/02/27/new-ranks-ncbi-taxonomy/)
                2. For taxonomic propagation of Archaea, Bacteria, and Eukaryota, we recommend to use domain,kingdom,phylum,class,order,family,genus,species for -r or --ranks
                3. For taxonomic propagation of Virus, we recommend to use realm,kingdom,phylum,class,order,family,genus,species for -r or --ranks
            
        ''')
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('-i', '--inputfasta', metavar='FILE', dest='infile_fasta_path',
                           help='Input FASTA file with NCBI accessions')
    input_group.add_argument('-L', '--list', metavar='FILE', dest='infile_list_path',
                           help='Input accession list (one per line)')
    
    # Output options
    parser.add_argument('-o', '--outputfile', metavar='FILE', dest='outfile_path',
                      help='Output taxonomy file')
    parser.add_argument('-g', '--outputlog', metavar='FILE', dest='logfile_path',
                      help='Output log file')
    parser.add_argument('-f', '--foverwrite', action='store_true', dest='force_overwrite',
                      help='Overwrite existing files')
    
    # Taxonomy database options
    parser.add_argument('-n', '--nodes', metavar='DIR', dest='ncbi_taxonomy_dir', default='./',
                      help='Directory containing NCBI taxonomy files')
    parser.add_argument('-a', '--acc2taxid', metavar='FILE', dest='infile_acc2taxid_path',
                      default='./nucl_gb.accession2taxid',
                      help='Accession to taxid mapping file')
    
    # Taxonomy ranks
    parser.add_argument('-r', '--ranks', metavar='RANKS', dest='output_ranks', 
                      default='domain,phylum,class,order,family,genus,species',
                      help='Taxonomic ranks to include')
    
    # Cache options
    parser.add_argument('--cache-dir', metavar='DIR', dest='cache_dir',
                      help='Directory for cache files (default: system temp directory)')
    parser.add_argument('--no-cache', action='store_true', dest='no_cache',
                      help='Disable caching and resume functionality')
    
    # API options
    parser.add_argument('--api-retries', type=int, default=3,
                      help='API retry attempts (default: 3)')
    parser.add_argument('--api-delay', type=float, default=0.34,
                      help='Delay between API calls (default: 0.34)')
    parser.add_argument('--no-api', action='store_true',
                      help='Disable API fallback')
    parser.add_argument('--email', dest='ncbi_email', required=True,
                      help='Email address for NCBI API (required). NOTE: We do not collect your email! The email is required per NCBI access rules. See: https://www.ncbi.nlm.nih.gov/books/NBK25497/')
    parser.add_argument('--batch-size', type=int, default=50,
                      help='Number of accessions to process per API batch (default: 50)')
    
    # Debug
    parser.add_argument('-d', '--debug', dest='debug_mode', action='store_true',
                      help='Enable debug output')
    
    args = parser.parse_args()
    
    # Disable cache if requested
    if args.no_cache:
        args.cache_dir = None
    
    # Process
    processor = TaxonomyProcessor(args)
    processor.run()


if __name__ == "__main__":
    main()

    