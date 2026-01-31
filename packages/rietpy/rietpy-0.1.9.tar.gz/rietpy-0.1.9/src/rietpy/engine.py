import subprocess
import os
import shutil
import re
from .constants import DEFAULT_RIETAN_DIR_WIN


class RietanEngine:
    def __init__(self, rietan_path="RIETAN", cif2ins_path="cif2ins"):
        """
        Initialize the Rietan engine.

        Args:
            rietan_path (str): Path to the RIETAN executable.
            cif2ins_path (str): Path to the cif2ins executable.
        """
        self.rietan_path = self._resolve_executable(rietan_path)
        self.cif2ins_path = self._resolve_executable(cif2ins_path)

    def _resolve_executable(self, exe_name):
        """
        Resolves the executable path, checking common locations if not found in PATH.
        """
        resolved = shutil.which(exe_name)
        if resolved:
            return resolved

        # Check common Windows location
        if os.name == "nt":
            candidate = os.path.join(DEFAULT_RIETAN_DIR_WIN, exe_name)
            if not candidate.lower().endswith(".exe"):
                candidate += ".exe"

            if os.path.exists(candidate):
                return candidate

        return exe_name

    def run(self, ins_file):
        """
        Runs RIETAN-FP with the given .ins file.

        Args:
            ins_file (str): Path to the .ins input file.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not os.path.exists(ins_file):
            print(f"Error: Input file '{ins_file}' not found.")
            return False

        ins_file = os.path.abspath(ins_file)
        working_dir = os.path.dirname(ins_file)
        file_name = os.path.basename(ins_file)

        # Ensure 'asfdc' file is present in the working directory
        # RIETAN requires this file for atomic scattering factors
        self._ensure_asfdc(working_dir)

        # Set environment variable for RIETAN if needed
        # Some versions might look for auxiliary files based on this
        env = os.environ.copy()
        rietan_exe = shutil.which(self.rietan_path)
        if rietan_exe:
            rietan_dir = os.path.dirname(os.path.abspath(rietan_exe))
            env["RIETAN"] = rietan_dir
            # Also add to PATH just in case
            env["PATH"] = rietan_dir + os.pathsep + env.get("PATH", "")

        # RIETAN typically expects the filename without extension
        # or handles it. To be safe and standard, we pass the base name without extension.
        # But we must ensure we are passing what it expects.
        # If file_name is "sample.ins", we pass "sample".
        base_name_no_ext = os.path.splitext(file_name)[0]

        # Construct arguments list based on RIETAN.command
        # "$RIETAN/rietan" $sample.ins $sample.int $sample.bkg $sample.itx $sample.hkl $sample.xyz $sample.fos $sample.ffe $sample.fba $sample.ffi $sample.ffo $sample.vesta $sample.plt $sample.gpd $sample.alb $sample.prf $sample.inflip $sample.exp
        extensions = [
            ".ins",
            ".int",
            ".bkg",
            ".itx",
            ".hkl",
            ".xyz",
            ".fos",
            ".ffe",
            ".fba",
            ".ffi",
            ".ffo",
            ".vesta",
            ".plt",
            ".gpd",
            ".alb",
            ".prf",
            ".inflip",
            ".exp",
        ]

        args = [base_name_no_ext + ext for ext in extensions]
        cmd = [self.rietan_path] + args

        print(f"Running RIETAN in {working_dir}...")

        try:
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                check=True,
                env=env,
            )

            # Write stdout to .lst file
            lst_file = os.path.join(working_dir, base_name_no_ext + ".lst")
            with open(lst_file, "w", encoding="utf-8") as f:
                f.write(result.stdout)

            print("RIETAN execution completed.")
            # print("Standard Output:\n", result.stdout)
            # print("Standard Error:\n", result.stderr)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error running RIETAN: {e}")
            print("Standard Output:\n", e.stdout)
            print("Standard Error:\n", e.stderr)
            return False
        except FileNotFoundError:
            print(f"Error: Executable '{self.rietan_path}' not found.")
            return False
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False

    def _ensure_asfdc(self, target_dir):
        """
        Ensures that the 'asfdc' file exists in the target directory.
        It tries to find it in the directory where the RIETAN executable resides.
        """
        target_path = os.path.join(target_dir, "asfdc")
        if os.path.exists(target_path):
            return

        # Find RIETAN executable path
        rietan_exe = shutil.which(self.rietan_path)
        if not rietan_exe:
            # If not in PATH, maybe it's a direct path
            if os.path.exists(self.rietan_path):
                rietan_exe = self.rietan_path
            else:
                print("Warning: Could not locate RIETAN executable to find 'asfdc'.")
                return

        rietan_dir = os.path.dirname(os.path.abspath(rietan_exe))
        source_path = os.path.join(rietan_dir, "asfdc")

        if os.path.exists(source_path):
            try:
                print(f"Copying 'asfdc' from {source_path} to {target_dir}...")
                shutil.copy(source_path, target_path)
            except Exception as e:
                print(f"Warning: Failed to copy 'asfdc': {e}")
        else:
            print(
                f"Warning: 'asfdc' file not found in {rietan_dir}. RIETAN might fail."
            )

    def run_cif2ins(self, cif_file, template_ins="template.ins"):
        """
        Runs cif2ins to generate .ins file from .cif and template.

        Args:
            cif_file (str): Path to the .cif input file.
            template_ins (str): Path to the template .ins file.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not os.path.exists(cif_file):
            print(f"Error: CIF file '{cif_file}' not found.")
            return False

        cif_file = os.path.abspath(cif_file)
        working_dir = os.path.dirname(cif_file)
        sample_name = os.path.splitext(os.path.basename(cif_file))[0]

        # Check template
        # If template_ins is just a filename, look in working_dir
        # If it's a path, use it.
        if os.path.dirname(template_ins):
            template_path = template_ins
        else:
            template_path = os.path.join(working_dir, template_ins)

        if not os.path.exists(template_path):
            print(f"Error: Template file '{template_path}' not found.")
            return False

        # Check for #std in cif file
        standardize = "0"
        try:
            with open(cif_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if re.search(r"^\s*#\s*std\s*$", content, re.MULTILINE):
                    standardize = "1"
        except Exception:
            pass

        # Construct command
        # cif2ins [0|1] ${sample}.cif template.ins ${sample}.ins ...

        output_ins = f"{sample_name}.ins"

        # Output filenames
        args = [
            standardize,
            os.path.basename(cif_file),
            os.path.basename(template_path),
            output_ins,
            f"{sample_name}-report.tex",
            f"{sample_name}.pdf",
            f"{sample_name}-struct.pdf",
            f"{sample_name}.lst",
            f"{sample_name}-mscs.pdf",
            f"{sample_name}-density.pdf",
        ]

        cmd = [self.cif2ins_path] + args

        # Set environment variable CIF2INS
        env = os.environ.copy()
        cif2ins_exe = shutil.which(self.cif2ins_path)
        if cif2ins_exe:
            cif2ins_dir = os.path.dirname(os.path.abspath(cif2ins_exe))
            env["CIF2INS"] = cif2ins_dir
            env["PATH"] = cif2ins_dir + os.pathsep + env.get("PATH", "")

        print(f"Running cif2ins in {working_dir}...")

        try:
            # Run without check=True to handle non-zero exit codes
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )

            # Check if output file exists
            output_path = os.path.join(working_dir, output_ins)

            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                if result.returncode != 0:
                    print(
                        f"Warning: cif2ins exited with code {result.returncode}, but output file was created."
                    )
                return True
            else:
                print(f"Error: cif2ins failed. Exit code: {result.returncode}")
                print("Standard Output:\n", result.stdout)
                print("Standard Error:\n", result.stderr)
                return False

        except FileNotFoundError:
            print(f"Error: Executable '{self.cif2ins_path}' not found.")
            return False

    def _detect_phase_ids(self, lines):
        """
        Detects phase IDs used in a file by scanning for @X pattern.
        Returns a set of phase IDs found (as strings).
        Ignores comments (lines starting with ! or #, or content after them).
        """
        ids = set()
        for line in lines:
            # Strip comments
            # RIETAN comments start with ! or #
            # We must handle cases where ! or # are inside strings? 
            # RIETAN strings are '...'.
            # Simple approach: split by ! then #
            
            # Simple stripping (effective for most cases)
            code_part = line.split('!')[0].split('#')[0]
            
            # Search in code part only
            # Using \b to ensure word boundary if possible, but @ is a separator.
            # Match @ followed by digits only (phase IDs are numeric)
            matches = re.findall(r"@(\d+)", code_part)
            for m in matches:
                ids.add(m)
        return ids

    def combine_ins_files(self, base_ins, other_ins_list, output_ins):
        """
        Combines multiple .ins files into a single multi-phase .ins file.
        References logic from Combins.command but adapted for standard .ins files.

        Args:
            base_ins (str): Path to the first .ins file (Phase 1).
            other_ins_list (list): List of paths to other .ins files (Phase 2, 3, ...).
            output_ins (str): Path to the output .ins file.
        """
        if not os.path.exists(base_ins):
            print(f"Error: Base file '{base_ins}' not found.")
            return False

        # Read base file
        with open(base_ins, "r", encoding="utf-8", errors="ignore") as f:
            base_lines = f.readlines()

        # Replace @N patterns in base file with @1 (Phase 1)
        base_lines = self._replace_n_patterns(base_lines, 1)

        # Validate Base Phase IDs (non-blocking)
        base_phase_ids = self._detect_phase_ids(base_lines)

        # Capture Constraint Template (from base file)
        # We assume base file *might* have a generic @N constraint block if it's a template?
        # BUT if we are detecting phase IDs, the base file should already have specific IDs (e.g. @1).
        # If it has @N, _detect_phase_ids would have raised ValueError.
        # So base file has valid numeric IDs.
        # Constraints are usually at the end. We will copy them as is for the base phases.

        # Initialize elements set
        all_elements = set()

        def extract_elements_from_line(line):
            # Extract element symbols (letters), ignoring / and whitespace
            # Standard RIETAN format: Ca P O F /
            return re.findall(r"\b[A-Za-z]+\b", line)

        # Extract elements from Base
        for i, line in enumerate(base_lines):
            if "! Elements @" in line:
                if i + 1 < len(base_lines):
                    all_elements.update(extract_elements_from_line(base_lines[i + 1]))

        # Prepare structure to build final file
        # We start with base_lines, but we need to inject content from other files.
        # Injection points:
        # 1. After Phase Blocks (Header) for base phase(s).
        # 2. After Parameter Blocks for base phase(s).
        # 3. After Constraints for base phase(s).

        # Find markers in Base
        phase_blocks_end_idx = -1
        param_blocks_end_idx = -1
        constraints_end_idx = -1

        # Scan for markers
        for i, line in enumerate(base_lines):
            if "} End of information about phases" in line:
                phase_blocks_end_idx = i
            if "} End of lines for label/species" in line:
                param_blocks_end_idx = i
            if "} End of linear constraints" in line:
                constraints_end_idx = i

        if phase_blocks_end_idx == -1 or param_blocks_end_idx == -1:
            print("Error: Could not find block end markers in base .ins file.")
            return False

        # Split Base into sections
        # Header + Phase Blocks
        final_lines = base_lines[:phase_blocks_end_idx]

        # New Phase Blocks go here

        # Middle (end of phases marker ... start of next block)
        # Actually base_lines[phase_blocks_end_idx] is the closing brace line.
        # It should be appended AFTER all phase blocks.

        middle_section = base_lines[phase_blocks_end_idx:param_blocks_end_idx]

        # New Param Blocks go here?
        # Wait, param_blocks_end_idx is the closing brace for params.

        # Footer (end of params ... end of file)
        footer_section = base_lines[param_blocks_end_idx:]

        # Process Other Files
        other_phase_blocks = []
        other_param_blocks = []
        other_constraint_blocks = []

        active_phases = set(base_phase_ids)

        for other_ins in other_ins_list:
            if not os.path.exists(other_ins):
                print(f"Warning: File '{other_ins}' not found. Skipping.")
                continue

            with open(other_ins, "r", encoding="utf-8", errors="ignore") as f:
                other_lines = f.readlines()

            pids = self._detect_phase_ids(other_lines)
            
            # Determine phase number for this file BEFORE updating active_phases
            # active_phases currently contains phase IDs from base + previously processed files
            next_phase_num = len(active_phases) + 1
            
            # Now update active_phases for validation
            active_phases.update(pids)

            # Extract elements
            for i, line in enumerate(other_lines):
                if "! Elements @" in line:
                    if i + 1 < len(other_lines):
                        all_elements.update(
                            extract_elements_from_line(other_lines[i + 1])
                        )

            # Extract Phase Blocks
            p_blocks = self._extract_phase_blocks(other_lines)
            if p_blocks:
                
                for blk in p_blocks:
                    # Replace @N patterns with actual phase number
                    renamed_block = self._replace_n_patterns(blk, next_phase_num)
                    other_phase_blocks.extend(renamed_block)
                    other_phase_blocks.append("\n")  # Spacer

            # Extract Parameter Block
            # We look for the main parameter section
            p_start = -1
            p_end = -1
            for i, line in enumerate(other_lines):
                if "Label, A(I), and ID(I) now starts here" in line:
                    p_start = i
                if "} End of lines for label/species" in line:
                    p_end = i

            if p_start != -1 and p_end != -1:
                # Extract content inside braces.
                # However, the file layout typically has { at start line and } at end line.
                # Content is between them.
                # But we need to filter out Global Params (SHIFT, ROUGH, BACKGROUND) if they are duplicated?
                # Usually we want Phase specific params (SCALE... etc)
                # Heuristic: Find first SCALE line?
                scale_idx = -1
                for k in range(p_start, p_end):
                    if "SCALE" in other_lines[k]:
                        scale_idx = k
                        break

                if scale_idx != -1:
                    # Look for preceding comment like "! Phase #2" or "Phase @2"
                    # Capture from slightly before SCALE if possible to get comment header
                    start_extract = scale_idx
                    if scale_idx > 0 and (
                        "Phase" in other_lines[scale_idx - 1]
                        or "!" in other_lines[scale_idx - 1]
                    ):
                        start_extract = scale_idx - 1

                    block = other_lines[start_extract:p_end]
                    # Replace @N patterns before adding to other_param_blocks
                    # Use the pre-calculated next_phase_num from above
                    renamed_block = self._replace_n_patterns(block, next_phase_num)
                    other_param_blocks.extend(renamed_block)
                else:
                    print(
                        f"Warning: Could not find SCALE in '{other_ins}'. Extracting whole block."
                    )
                    # If no SCALE found, maybe it's minimal?
                    block = other_lines[p_start + 1 : p_end]
                    renamed_block = self._replace_n_patterns(block, next_phase_num)
                    other_param_blocks.extend(renamed_block)

            # Extract Constraints
            # Check for "Linear constraints" section
            c_start = -1
            c_end = -1
            for i, line in enumerate(other_lines):
                if "Linear constraints" in line and "{" in line:  # Start of section
                    pass  # Usually logic below handles inside
                if "! Linear constraints" in line:  # Header
                    pass

                # Constraints are between "ID(I) = 2." logic and "}."
                # Usually standard RIETAN file:
                # ! Linear constraints
                # If NMODE <> 1
                # ...
                # } End of linear constraints.

                # We need to capture lines that look like constraints: A(...)=...
                # Or marked with "! Constraints @X"
                # If the user uses explicit markers, we trust them.

            # Simple approach: Find "! Constraints @X" blocks inside the file
            # or extract all valid constraint lines if no markers?
            # Assuming file follows @X convention:
            for i, line in enumerate(other_lines):
                if "! Constraints @" in line:
                    # Found a block start
                    # Find end of this block "# End Constraints"
                    blk_end = -1
                    for j in range(i + 1, len(other_lines)):
                        if "# End Constraints @" in other_lines[j]:
                            blk_end = j
                            break

                    if blk_end != -1:
                        constraint_block = other_lines[i : blk_end + 1]
                        # Replace @N patterns using the pre-calculated next_phase_num
                        renamed_constraints = self._replace_n_patterns(constraint_block, next_phase_num)
                        other_constraint_blocks.extend(renamed_constraints)

        # Construct Final Content

        # 1. Header + Base Phase Blocks
        # 2. Other Phase Blocks
        # 3. Closing brace for phases

        merged_header = final_lines + other_phase_blocks

        # 4. Global Params + Base Param Blocks (middle_section)
        # middle_section starts with closing brace of phases }
        # ends with closing brace of params }

        # We need to insert other params BEFORE the closing brace of params.

        mp_lines = middle_section + footer_section

        # Find param closing brace in mp_lines to insert before it
        # Actually footer_section starts at param_blocks_end_idx which IS the closing key.
        # So we can just append to middle_section?
        # middle_section includes the closing brace of phases. Correct.
        # And goes UP TO param_blocks_end_idx (exclusive).
        # So it contains the content of base params.

        # Wait, base_lines[param_blocks_end_idx] is the "}" line.
        # So middle_section is: "}" (end phases) ... ... ... (last param line).

        # So we append other_param_blocks AFTER middle_section.

        merged_params = middle_section + other_param_blocks

        # 5. Footer (closes params }, then constraints etc)
        # footer_section starts with "}" (end params).

        # Check constraints in footer
        # We need to inject other_constraint_blocks before "} End of linear constraints"

        # Parse footer to find insertion point
        constr_close_idx = -1
        for i, line in enumerate(footer_section):
            if "} End of linear constraints" in line:
                constr_close_idx = i
                break

        if constr_close_idx != -1:
            # Insert before closing brace
            merged_footer = (
                footer_section[:constr_close_idx]
                + other_constraint_blocks
                + footer_section[constr_close_idx:]
            )
        else:
            # If no constraint block found in base, append others at end?
            # Probably base has no constraints section if NMODE=1?
            # Just append.
            merged_footer = footer_section + other_constraint_blocks

        result_lines = merged_header + merged_params + merged_footer

        # Post-process: Update Elements
        # Find "! Elements @" line and update next line
        if all_elements:
            sorted_elements = sorted(list(all_elements))
            quoted_elements = [f"'{el}'" for el in sorted_elements]
            new_element_line = "  " + "  ".join(quoted_elements) + " /\n"

            # Scan result_lines to update
            # Note: Phase 1 block is in merged_header. Other phases were appended.
            # Usually elements are only listed in Phase 1 block?
            # Or does each phase have its own virtual/real species list?
            # "Data concerning crystalline phases ... "
            # usually Elements are global or per phase?
            # In multi_phase.ins:
            # "Real chemical species" -> Global? NO, inside "Data concerning..."?
            # Actually typically 'Element' list is before "Data concerning".
            # No, RIETAN structure:
            # Titles...
            # Radiation...
            # ...
            # Real chemical species (Elements)
            # Virtual chemical species
            # Data concerning crystalline phases { ... }

            # The "Real chemical species" section is BEFORE the phase blocks.
            # My 'final_lines' captured 'base_lines[:phase_blocks_end_idx]'.
            # 'phase_blocks_end_idx' matches "} End of information about phases".
            # So 'final_lines' includes the Elements section.

            for i, line in enumerate(result_lines):
                if "Real chemical species" in line and not line.strip().startswith("!"):
                    # This is a header comment usually.
                    pass

                # We look for specific line we want to replace?
                # Actually, standard RIETAN input for elements looks like:
                # 'Fe' 'O' /
                # It doesn't have a strict keyword prefix.
                # But 'base_lines' extraction logic used "! Elements @"?
                # Ah, Combins.command uses "! Elements @".
                # Standard RIETAN doesn't have "! Elements @".
                # If 'base_ins' is a standard file, search for lines with chemical symbols?
                # "Real chemical species" section is usually marked by comments.
                # If we rely on valid RIETAN lines:
                # 'Si' 'O' 'Na' /

                # If we cannot confidently find the line, we might skip updating it unless we know it needs update.
                # combine_ins_files docstring says "References logic from Combins.command".
                # Combins.command assumes specific comments.
                pass

        # Update NPHASE
        total_phases = len(active_phases)
        for i, line in enumerate(result_lines):
            if "NPHASE" in line and "=" in line:
                # Standard regex replacement
                # NPHASE = 1  or  NPHASE@ = 1
                # Be careful not to match NPHASE somewhere else
                if re.match(r"^\s*NPHASE", line):
                    # Replace the number
                    line = re.sub(r"=\s*\d+", f"= {total_phases}", line, count=1)
                    result_lines[i] = line
                    break

        # Post-validation of generated file content
        invalid_ids = set()
        for pid in active_phases:
            if not pid.isdigit():
                invalid_ids.add(pid)

        # To truly check output, we should scan 'result_lines'.
        final_file_phase_ids = set()
        for line in result_lines:
             code_part = line.split('!')[0].split('#')[0]
             matches = re.findall(r"@(\d+)", code_part)
             final_file_phase_ids.update(matches)
        
        output_invalid_ids = [pid for pid in final_file_phase_ids if not pid.isdigit()]
        
        if output_invalid_ids:
            print(f"Error: Non-numeric phase IDs found in combined output: {output_invalid_ids}")
            return False

        try:
            with open(output_ins, "w", encoding="utf-8") as f:
                f.writelines(result_lines)
            print(f"Successfully created multi-phase .ins file: {output_ins}")
            return True
        except Exception as e:
            print(f"Error writing output file: {e}")
            return False

    def _extract_phase_blocks(self, lines):
        """
        Extracts individual phase blocks from the header section.
        Returns a list of lists of strings (blocks).
        """
        blocks = []
        current_block = []
        in_block = False

        start_idx = -1
        end_idx = -1
        for i, line in enumerate(lines):
            if "Data concerning crystalline phases" in line:
                start_idx = i
            if "} End of information about phases" in line:
                end_idx = i

        if start_idx == -1 or end_idx == -1:
            return []

        for i in range(start_idx + 1, end_idx):
            line = lines[i]
            # Check for start of block
            # Usually "! Phase @" or "PHNAME"
            if "! Phase @" in line:
                if in_block:
                    # End previous block
                    blocks.append(current_block)
                    current_block = []
                in_block = True
                current_block.append(line)
            elif in_block:
                current_block.append(line)
                # Check for end of block
                if "# End Phase" in line:
                    in_block = False
                    blocks.append(current_block)
                    current_block = []

        # Handle case where last block doesn't have explicit end marker or we are inside one
        if in_block and current_block:
            blocks.append(current_block)

        return blocks

    def _rename_phase_block(self, lines, phase_num):
        """Renames variables in the phase block for the new phase number."""
        new_lines = []
        for line in lines:
            # Skip empty lines or lines that are just comments if desired? No, keep them.

            # Rename PHNAME1 -> PHNAME{n}
            # Regex for variables ending in 1
            # PHNAME, HKLM, LPAIR, INDIV, IHA, IKA, ILA
            # IHP, IKP, ILP are special (vectors)

            # General rule: VAR1 = ... -> VAR{n} = ...
            # But be careful not to match values.

            # Specific replacements
            line = re.sub(r"(PHNAME)1", f"\\g<1>{phase_num}", line)
            line = re.sub(r"(VNS)1", f"\\g<1>{phase_num}", line)
            line = re.sub(r"(HKLM)1", f"\\g<1>{phase_num}", line)
            line = re.sub(r"(LPAIR)1", f"\\g<1>{phase_num}", line)
            line = re.sub(r"(INDIV)1", f"\\g<1>{phase_num}", line)
            line = re.sub(r"(IHA)1", f"\\g<1>{phase_num}", line)
            line = re.sub(r"(IKA)1", f"\\g<1>{phase_num}", line)
            line = re.sub(r"(ILA)1", f"\\g<1>{phase_num}", line)

            # Vectors: IHP1 -> IHP{n}1 (Phase n, Vector 1)
            # Assuming source is Phase 1
            line = re.sub(r"(IHP)([0-9]+)", f"\\g<1>{phase_num}\\g<2>", line)
            line = re.sub(r"(IKP)([0-9]+)", f"\\g<1>{phase_num}\\g<2>", line)
            line = re.sub(r"(ILP)([0-9]+)", f"\\g<1>{phase_num}\\g<2>", line)

            new_lines.append(line)
        return new_lines

    def _rename_param_block(self, lines, phase_num):
        """Renames labels in the parameter block for the new phase number."""
        new_lines = []
        for line in lines:
            # SCALE -> SCALE{n}
            # PREF -> PREF{n}
            # CELLQ -> CELLQ{n}

            # If source is Phase 1, SCALE might be SCALE or SCALE1?
            # In Fapatite.ins, it is SCALE.
            # In Cu3Fe4P6.ins, it is SCALE1.
            # We should handle both.

            # Replace SCALE followed by space or 1
            line = re.sub(r"^(\s*)SCALE1?(\s+)", f"\\g<1>SCALE{phase_num}\\g<2>", line)
            line = re.sub(r"^(\s*)PREF1?(\s+)", f"\\g<1>PREF{phase_num}\\g<2>", line)
            line = re.sub(r"^(\s*)CELLQ1?(\s+)", f"\\g<1>CELLQ{phase_num}\\g<2>", line)

            # Profile parameters: GAUSS01 -> GAUSS01{n}
            # List: GAUSS, LORENTZ, ASYM, ANISTR, FWHM, ETA, ANISOBR, DUMMY, M
            # We match Keyword + Digits
            # If digits end in 1 (Phase 1), replace 1 with n?
            # Or just append n?
            # Cu3Fe4P6: GAUSS01 -> GAUSS012.
            # So we append n.

            keywords = [
                "GAUSS",
                "LORENTZ",
                "ASYM",
                "ANISTR",
                "FWHM",
                "ETA",
                "ANISOBR",
                "DUMMY",
                "M",
            ]
            pattern = r"^(\s*)(" + "|".join(keywords) + r")([0-9]+)(\s+)"

            def repl(m):
                return f"{m.group(1)}{m.group(2)}{m.group(3)}{phase_num}{m.group(4)}"

            line = re.sub(pattern, repl, line)

            # Structure parameters: Label/Species
            # O1/O- -> O1_{n}/O-
            # Regex: ^(\s*)([A-Za-z0-9]+)(/[A-Za-z0-9+\-]+)
            # Exclude keywords

            # Check if it looks like a structure line
            if "/" in line and not line.strip().startswith("!"):
                # Avoid matching comments
                match = re.match(r"^(\s*)([A-Za-z0-9]+)(/[A-Za-z0-9+\-]+)", line)
                if match:
                    label = match.group(2)
                    # Don't rename if it's a keyword (unlikely with /)
                    # Rename label
                    new_label = f"{label}_{phase_num}"
                    line = line.replace(f"{label}/", f"{new_label}/", 1)

            new_lines.append(line)
        return new_lines

    def _replace_n_patterns(self, lines, phase_num):
        """
        Replace @N patterns with @{phase_num} in all lines.
        
        Handles patterns like:
        - SCALE@N → SCALE@1
        - GAUSS01@N → GAUSS01@2
        - PHNAME@N → PHNAME@3
        - ! Parameters @N → ! Parameters @1
        - ! Constraints @N → ! Constraints @2
        
        Args:
            lines (list): List of strings (lines) to process
            phase_num (int): Phase number to replace @N with
            
        Returns:
            list: Modified lines with @N replaced by @{phase_num}
        """
        new_lines = []
        for line in lines:
            # Replace @N with @{phase_num}
            # Use word boundary to avoid replacing @N in unintended contexts
            line = re.sub(r'@N\b', f'@{phase_num}', line)
            new_lines.append(line)
        return new_lines
