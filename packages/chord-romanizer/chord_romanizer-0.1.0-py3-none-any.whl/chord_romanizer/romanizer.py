from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Tuple, Union

from .chord_parser import NOTE_NAMES, ParsedChord, normalize_note_pc
from .note_speller import NoteSpeller, NATURAL_PITCH_CLASS, NOTE_LETTERS, SEMITONE_MAP
from .chord_structure import ChordStructure
from .chord_interpreter import ChordInterpreter, HybridAnalysis, HybridKind


@dataclass
class AnalysisNode:
    original_chord: ParsedChord
    effective_root: str
    effective_quality: str
    is_dominant: bool
    is_minor: bool
    is_diminished: bool
    # Metadata to be filled by pattern matching
    is_ii_v_start: bool = False
    is_resolution_target: bool = False
    resolution_type: Optional[str] = None


@dataclass
class ContextHint:
    prefer_sharps: Optional[bool] = None
    node: Optional[AnalysisNode] = None


@dataclass
class RomanizedChord:
    chord: ParsedChord
    roman: str
    alternate_labels: List[str]
    degree_root: str
    degree_bass: Optional[str] = None
    roman_root_bass: Optional[str] = None
    is_hybrid: bool = False
    alter: Optional[str] = None
    symbol_fixed: Optional[str] = None
    # Enhanced Analysis Metadata
    is_ii_v_start: bool = False
    is_resolution_target: bool = False
    resolution_type: Optional[str] = None


class Romanizer:
    MAJOR_SCALE_STEPS = [0, 2, 4, 5, 7, 9, 11]
    ROMAN_DEGREES = ["I", "II", "III", "IV", "V", "VI", "VII"]

    def __init__(self, default_tonic: str = "C"):
        self.default_tonic = default_tonic
        self.interpreter = ChordInterpreter()

    def annotate_progression(
        self, progression: Iterable[Union[ParsedChord, Tuple[ParsedChord, str]]]
    ) -> List[RomanizedChord]:
        # 入力を正規化: (chord, key) のリストにする
        sequence: List[Tuple[ParsedChord, str]] = []
        for item in progression:
            if isinstance(item, tuple):
                sequence.append(item)
            else:
                sequence.append((item, self.default_tonic))

        # Context解析用にChordだけのリストを作成
        chords_only = [item[0] for item in sequence]
        hints = self._analyze_global_context(chords_only)
        results = []

        for i, (chord, key) in enumerate(sequence):
            if not chord:
                continue
            prev_chord = sequence[i - 1][0] if i > 0 else None
            next_chord = sequence[i + 1][0] if i + 1 < len(sequence) else None
            hint = hints[i] if i < len(hints) else None

            result = self._process_chord(chord, key, prev_chord, next_chord, hint)
            if result:
                results.append(result)

        return results

    def _analyze_global_context(self, chords: List[ParsedChord]) -> List[ContextHint]:
        # 1. プレ解析: 実質的なルートと機能的なQualityを決定
        nodes = self._pre_analyze_progression(chords)
        
        # 2. パターンマッチング: II-V および解決の検出
        self._detect_ii_v_and_resolutions(nodes)

        hints = []
        for i, node in enumerate(nodes):
            hint = ContextHint(node=node)
            
            # --- 解析結果に基づくスペルロジック ---
            
            # デフォルト: 半音進行ロジック
            if i + 1 < len(nodes):
                next_node = nodes[i+1]
                dist = NoteSpeller.semitone_distance(next_node.effective_root, node.effective_root)
                if dist == 1:
                    hint.prefer_sharps = True
                elif dist == 11:
                    hint.prefer_sharps = False
            
            # Overwrite: II-V やドミナント解決の場合、解決先のキー（調号）を尊重する
            target_node = None
            if node.is_ii_v_start:
                # II -> V -> [Target]
                if i + 2 < len(nodes):
                    target_node = nodes[i+2]
            elif node.is_dominant and i + 1 < len(nodes):
                 # V -> [Target]
                next_node = nodes[i+1]
                dist = NoteSpeller.semitone_distance(next_node.effective_root, node.effective_root)
                if dist == 5:
                    target_node = next_node

            if target_node:
                pref = self._get_target_accidental_preference(target_node.effective_root)
                if pref is not None:
                    hint.prefer_sharps = pref

            hints.append(hint)

        return hints

    def _get_target_accidental_preference(self, root: str) -> Optional[bool]:
        """
        解決先のルート音に基づいて、その調における臨時記号の推奨（シャープorフラット）を返す。
        True=Sharp, False=Flat, None=Neutral
        """
        # 1. ルート自体の臨時記号
        if "b" in root: return False
        if "#" in root: return True
        
        # 2. ナチュラルキーの傾向 (Circle of Fifths)
        if root == "F": return False
        if root == "C": return None 
        if root in ("G", "D", "A", "E", "B"): return True
        return None

    def _pre_analyze_progression(self, chords: List[ParsedChord]) -> List[AnalysisNode]:
        nodes = []
        for chord in chords:
            # ハイブリッドコードの可能性を解釈
            # ここでは 'next_chord' が完全には分からないが、
            # 意味のある解析は通常コードの内部構造に依存するため、まずは単体で解析する。
            # "G/A" -> "A9sus4" のように、analyze_slash_chord は next_chord なしでも SUS4_9 を検出可能。
            analysis = self.interpreter.analyze_slash_chord(chord, None)
            
            effective_root = chord.root
            effective_quality = chord.quality or ""
            
            if analysis.is_hybrid:
                 # ドミナントとして機能するかチェック
                 if analysis.kind in (HybridKind.SUS4_9, HybridKind.SUS4_7_B9, HybridKind.SEC_DOM_3_IN_BASS):
                     # G/A -> A ドミナントとして振る舞う
                     effective_root = chord.bass # A
                     effective_quality = "7" # ドミナント機能として扱う
                 elif analysis.kind == HybridKind.HALFDIM_9:
                     # Fm/G -> G7sus4(b9) 通常 SUS4_7_B9 でカバーされるためここではスルー
                     pass 
            
            # フラグ決定
            is_dominant = ChordStructure.is_dominant_quality(effective_quality)
            is_minor = ChordStructure.is_minor_quality(effective_quality) 
            is_diminished = "dim" in effective_quality.lower() or "m7-5" in effective_quality.lower() or "m7b5" in effective_quality.lower()
            
            # ハイブリッド時のフラグ上書き
            if analysis.kind in (HybridKind.SUS4_9, HybridKind.SUS4_7_B9):
                is_dominant = True
            
            nodes.append(AnalysisNode(
                original_chord=chord,
                effective_root=effective_root,
                effective_quality=effective_quality,
                is_dominant=is_dominant,
                is_minor=is_minor,
                is_diminished=is_diminished
            ))
        return nodes

    def _detect_ii_v_and_resolutions(self, nodes: List[AnalysisNode]):
        for i in range(len(nodes) - 1):
            curr = nodes[i]
            nex = nodes[i+1]
            
            dist = NoteSpeller.semitone_distance(nex.effective_root, curr.effective_root)
            if dist is None: continue
            
            # --- II-V 判定 ---
            # 条件: Root が 5 上行 (または 7 下行) -> dist=5
            # Qualities: II=Minor/Dim系, V=Dominant系
            if dist == 5:
                if (curr.is_minor or curr.is_diminished) and nex.is_dominant:
                    curr.is_ii_v_start = True
            
            # --- 解決 (Resolution) 判定 ---
            # 現在が Dominant である場合をチェック
            if curr.is_dominant:
                # 1. 完全解決 (Perfect Resolution, V -> I): 5 上行
                if dist == 5:
                    nex.is_resolution_target = True
                    nex.resolution_type = "perfect"
                
                # 2. 半音解決 (Semitone Resolution, SubV -> I): 1 下行 (dist=11)
                elif dist == 11:
                     nex.is_resolution_target = True
                     nex.resolution_type = "semitone"

    def _process_chord(
        self, chord, key_tonic, prev_chord, next_chord, hint
    ) -> Optional[RomanizedChord]:
        dist = NoteSpeller.semitone_distance(chord.root, key_tonic)
        if dist is None:
            return None

        # 1) Root Roman 決定
        prefer_sharps = hint.prefer_sharps if hint else None
        base_degree, alternates = self._determine_degree_name(
            dist, key_tonic, chord, prev_chord, next_chord, prefer_sharps
        )

        primary_roman_root = self._format_roman(base_degree, chord.quality)
        alt_romans = [self._format_roman(a, chord.quality) for a in alternates]

        # 2) Slash/Hybrid 解析（Interpreter）
        analysis = self.interpreter.analyze_slash_chord(chord, next_chord)

        # 3) Root/Bass のスペリングを先に確定（ここが重要）
        root_fixed = self._spell_degree_note(base_degree, key_tonic)
        if analysis.root_override:
            root_fixed = analysis.root_override

        degree_bass: Optional[str] = None
        roman_root_bass: Optional[str] = None

        bass_fixed: Optional[str] = None
        bass_for_degree: Optional[str] = None

        redundant_bass = False
        if chord.bass:
            redundant_bass = self._same_pitch(chord.root, chord.bass)
            # (A) 転回形: コード構成音スペリングに合わせてベースを修正（E#など）
            if not analysis.is_hybrid:
                tones = ChordStructure.get_spelled_tones(
                    root_fixed or chord.root, chord.quality
                )
                bass_pitch_class = NoteSpeller.pitch_class_of(chord.bass)
                bass_fixed = tones.get(bass_pitch_class, chord.bass) if bass_pitch_class is not None else chord.bass
                bass_for_degree = bass_fixed

            # (B) ハイブリッド: Interpreter が決めた prefer に従って表記（Bb/A#など）
            else:
                bass_pitch_class = NoteSpeller.pitch_class_of(chord.bass)
                if analysis.bass_preference is not None and bass_pitch_class is not None:
                    bass_fixed = NoteSpeller.name_of_pitch_class(bass_pitch_class, analysis.bass_preference)
                else:
                    # 解決方向が取れない等なら入力表記を尊重（通常はBbのままにしたい）
                    bass_fixed = chord.bass
                bass_for_degree = bass_fixed

            # 4) degree_bass は「修正後の bass」から計算する（ここがズレ解消）
            if bass_for_degree:
                degree_bass = self._degree_from_spelling(bass_for_degree, key_tonic)

            # root/bass の複合度数は転回でも持っておく（検索・学習に便利）
            if degree_bass:
                roman_root_bass = f"{base_degree}/{degree_bass}"

        # 5) roman 表示をどうするか
        #    - スラッシュシンボルが来たら（転回でも） roman に /degree_bass を付ける
        roman_label = primary_roman_root
        if (
            chord.bass
            and degree_bass
            and ("/" in (chord.symbol or ""))
            and (not redundant_bass)
        ):
            roman_slash = f"{primary_roman_root}/{degree_bass}"
            roman_label = roman_slash
            # 互換：ベース無しも alternate に残す
            if primary_roman_root not in alt_romans:
                alt_romans.append(primary_roman_root)

        if redundant_bass:
            degree_bass = None
            roman_root_bass = None

        # 6) symbol_fixed も同じ root_fixed/bass_fixed で書き換え
        symbol_fixed = self._rewrite_symbol(
            chord.symbol, chord.root, root_fixed, chord.bass, bass_fixed
        )

        # Retrieve analysis metadata
        ii_v_start = hint.node.is_ii_v_start if hint and hint.node else False
        res_target = hint.node.is_resolution_target if hint and hint.node else False
        res_type = hint.node.resolution_type if hint and hint.node else None

        return RomanizedChord(
            chord=chord,
            roman=roman_label,
            alternate_labels=alt_romans,
            degree_root=base_degree,
            degree_bass=degree_bass,
            roman_root_bass=roman_root_bass,
            is_hybrid=analysis.is_hybrid,
            alter=self._romanize_absolute_symbol(analysis.alter, key_tonic) if analysis.alter else None,
            symbol_fixed=symbol_fixed,
            is_ii_v_start=ii_v_start,
            is_resolution_target=res_target,
            resolution_type=res_type
        )

    # --- Core Logic for Roman Naming (Business Logic) ---
    def _same_pitch(self, note_a: str, note_b: str) -> bool:
        pc_a = NoteSpeller.pitch_class_of(note_a)
        pc_b = NoteSpeller.pitch_class_of(note_b)
        if pc_a is None or pc_b is None:
            # 念のため normalize_note_pc でもフォールバック
            norm_a = normalize_note_pc(note_a)
            norm_b = normalize_note_pc(note_b)
            if norm_a is None or norm_b is None:
                return False
            pc_a = SEMITONE_MAP[norm_a]
            pc_b = SEMITONE_MAP[norm_b]
        return pc_a == pc_b

    def _determine_degree_name(
        self, dist: int, key_tonic: str, chord, prev_chord, next_chord, prefer_sharps
    ) -> Tuple[str, List[str]]:
        """距離と文脈から最適な度数名(#IV, bVなど)を決定する"""
        # トライトーンの特別処理
        if dist == 6:
            quality_lower = (chord.quality or "").lower()
            is_half_dim = "m7-5" in quality_lower or "m7b5" in quality_lower
            target_is_sharp = (
                prefer_sharps if prefer_sharps is not None else True
            )  # Default #IV
            if is_half_dim:
                target_is_sharp = True
            elif next_chord:
                dist_next = NoteSpeller.semitone_distance(next_chord.root, key_tonic)
                if dist_next == 5:
                    target_is_sharp = False  # -> IV (bV -> IV)

            main = "#IV" if target_is_sharp else "bV"
            alt = "bV" if target_is_sharp else "#IV"
            return main, [alt]

        # Neapolitan などの特殊ルール
        if dist == 1 and next_chord:  # bII check
            dist_next = NoteSpeller.semitone_distance(next_chord.root, key_tonic)
            if dist_next == 0:
                return "bII", []

        prefer = False if prefer_sharps is None else prefer_sharps

        # 通常計算
        base, _ = self._calc_degree_base(dist, prefer)
        # 異名同音の代替案を作成
        alt_base, _ = self._calc_degree_base(dist, not prefer)

        alternates = [alt_base] if base != alt_base else []
        return base, alternates

    def _calc_degree_base(
        self, dist: int, prefer_sharps: Optional[bool]
    ) -> Tuple[str, int]:
        # ★通常はフラット優先（None -> False）
        prefer = False if prefer_sharps is None else prefer_sharps

        best_score, best_idx, best_alt = 99, 0, 0
        for i, step in enumerate(self.MAJOR_SCALE_STEPS):
            delta = (dist - step + 12) % 12
            alt = delta if delta <= 6 else delta - 12
            score = abs(alt)

            if score < best_score:
                best_score, best_idx, best_alt = score, i, alt
            elif score == best_score:
                # ★tie-break: prefer に従う（Falseならフラット側=より負のalt）
                if prefer is True and alt > best_alt:
                    best_idx, best_alt = i, alt
                elif prefer is False and alt < best_alt:
                    best_idx, best_alt = i, alt

        acc = "#" if best_alt == 1 else "b" if best_alt == -1 else ""
        if abs(best_alt) > 1:
            acc = ("#" * best_alt) if best_alt > 0 else ("b" * -best_alt)

        return f"{acc}{self.ROMAN_DEGREES[best_idx]}", best_alt

    def _format_roman(self, degree: str, quality: str) -> str:
        # #IV + m7 -> #IVm7
        acc = degree[0] if degree[0] in "#b" else ""
        body = degree[1:] if acc else degree
        
        # Display Mapping
        display_quality = quality.replace("maj7", "M7").replace("ma7", "M7")
        
        return f"{acc}{body}{display_quality}"

    def _get_degree_label_simple(self, note: str, key_tonic: str) -> Optional[str]:
        d = NoteSpeller.semitone_distance(note, key_tonic)
        if d is None:
            return None
        base, _ = self._calc_degree_base(d, None)
        return base

    def _degree_from_spelling(self, note: str, key_tonic: str) -> Optional[str]:
        """
        入力の綴り（文字名）を優先して度数を決める。
        例: tonic=C, note=E# -> #III（F ではなく）
            tonic=C, note=Bb -> bVII（A# ではなく）
        """
        note_parsed = NoteSpeller.parse_note(note)
        tonic_parsed = NoteSpeller.parse_note(key_tonic)
        if note_parsed is None or tonic_parsed is None:
            return None

        note_letter, _ = note_parsed
        tonic_letter, tonic_accidental = tonic_parsed

        # degree index は文字の差で確定（綴り優先の肝）
        degree_index = (
            NOTE_LETTERS.index(note_letter) - NOTE_LETTERS.index(tonic_letter)
        ) % 7

        # その度数の「ダイアトニック想定PC」を作る（メジャー基準）
        tonic_pc = (NATURAL_PITCH_CLASS[tonic_letter] + tonic_accidental) % 12
        expected_pc = (tonic_pc + self.MAJOR_SCALE_STEPS[degree_index]) % 12

        # 実PCとの差分が accidental
        actual_pc = NoteSpeller.pitch_class_of(note)
        if actual_pc is None:
            return None

        diff = (actual_pc - expected_pc) % 12
        if diff > 6:
            diff -= 12  # signed shortest

        # 通常はフラット優先…という話は「同音異綴り」では入力綴りが勝つのでここでは不要
        if diff == 0:
            acc = ""
        elif diff > 0:
            acc = "#" * diff
        else:
            acc = "b" * (-diff)

        return f"{acc}{self.ROMAN_DEGREES[degree_index]}"

    def _spell_degree_note(self, degree: str, key_tonic: str) -> Optional[str]:
        """
        度数表記 (例: "#IV") と現在のTonic (例: "C") から、
        実音 (例: "F#") を復元する。
        """
        if not degree:
            return None

        # 1. 度数文字列のパース (例: "#IV" -> acc=+1, body="IV")
        acc_val = 0
        i = 0
        while i < len(degree) and degree[i] in ("#", "b"):
            acc_val += 1 if degree[i] == "#" else -1
            i += 1

        roman_body = degree[i:]
        if roman_body not in self.ROMAN_DEGREES:
            return None

        degree_index = self.ROMAN_DEGREES.index(roman_body)  # 0..6 (I..VII)

        # 2. Tonic情報の取得
        tonic_parsed = NoteSpeller.parse_note(key_tonic)
        if tonic_parsed is None:
            return None
        tonic_letter, tonic_accidental = tonic_parsed

        # Tonicのピッチクラスを計算
        tonic_base_pc = NATURAL_PITCH_CLASS[tonic_letter]
        tonic_pc = (tonic_base_pc + tonic_accidental) % 12

        # 3. ターゲット音の計算
        # ピッチクラス: Tonic + スケール上の半音幅 + 臨時記号
        scale_step_semitones = self.MAJOR_SCALE_STEPS[degree_index]
        target_pc = (tonic_pc + scale_step_semitones + acc_val) % 12

        # 文字(Letter): Tonic + スケール上の文字数
        target_letter = NoteSpeller.shift_letter(tonic_letter, degree_index)

        # 4. スペリング
        # 文字とPCから、正しい臨時記号付きの文字列を生成
        return NoteSpeller.spell_pitch_class(target_letter, target_pc)

    def _rewrite_symbol(
        self,
        symbol: str,
        root_old: str,
        root_new: Optional[str],
        bass_old: Optional[str],
        bass_new: Optional[str],
    ) -> str:
        """コードシンボルの文字列を新しいRoot/Bass表記で置換する。"""
        s = symbol
        if root_new and s.startswith(root_old):
            s = root_new + s[len(root_old) :]
        if "/" in s and bass_old and bass_new:
            head, tail = s.split("/", 1)
            if tail.startswith(bass_old):
                tail = bass_new + tail[len(bass_old) :]
            s = head + "/" + tail
        return s

    def _romanize_absolute_symbol(self, symbol: str, key_tonic: str) -> Optional[str]:
        """
        ChordInterpreterが返す絶対音名付きのシンボル(例: 'G9sus4')を、
        現在のキーに基づいたローマ数字表記(例: 'V9sus4')に変換する。
        """
        # Handle slash
        parts = symbol.split("/")
        root_part = parts[0]
        bass_part = parts[1] if len(parts) > 1 else None
        
        # Parse root part to separate Note vs Suffix
        root_note, suffix = self._split_note_and_suffix(root_part)
        if not root_note: return symbol # Fallback
        
        degree = self._degree_from_spelling(root_note, key_tonic)
        if not degree: return symbol
        
        # Format roman
        # degree like "#IV", suffix like "m7" -> "#IVm7"
        acc = degree[0] if degree[0] in "#b" else ""
        body = degree[1:] if acc else degree
        
        roman_root = f"{acc}{body}{suffix}"
        
        if bass_part:
             bass_degree = self._degree_from_spelling(bass_part, key_tonic)
             if bass_degree:
                 return f"{roman_root}/{bass_degree}"
                 
        return roman_root

    def _split_note_and_suffix(self, text: str) -> Tuple[Optional[str], str]:
        """文字列先頭の音名(C, C#, Dbなど)と、それ以降(9sus4など)を分離する"""
        if not text: return None, ""
        # 1. Letter
        if text[0].upper() not in NOTE_LETTERS: return None, text
        
        # 2. Accidentals (#, b)
        # NoteSpeller uses replace("x", "##") internally but here we expect output from NoteSpeller
        # so mostly # or b.
        i = 1
        while i < len(text):
            c = text[i]
            if c in ("#", "b"): 
                i += 1
            else:
                break
        return text[:i], text[i:]
