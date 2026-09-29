"""Tests for the BM25 tokenizer."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tokenizer import tokenize


class TestTokenizerBasics:
    def test_empty_string(self):
        assert tokenize("") == []

    def test_simple_words(self):
        result = tokenize("Java Spring Boot developer")
        assert "java" in result
        assert "spring_boot" in result
        assert "developer" in result

    def test_lowercase(self):
        result = tokenize("JAVA SPRING DEVELOPER")
        assert "java" in result
        assert "developer" in result


class TestAccentFolding:
    def test_french_accents(self):
        result = tokenize("système développement réseau")
        assert "systeme" in result
        assert "developpement" in result
        assert "reseau" in result

    def test_accent_matching(self):
        """système and systeme should produce the same token."""
        r1 = tokenize("système")
        r2 = tokenize("systeme")
        assert r1 == r2


class TestTechTokens:
    def test_csharp(self):
        result = tokenize("Développeur C# expérimenté")
        assert "c#" in result

    def test_dotnet(self):
        result = tokenize("Framework .NET Core pour applications web")
        assert ".net_core" in result

    def test_nodejs(self):
        result = tokenize("Backend avec Node.js et Express.js")
        assert "node.js" in result
        assert "express.js" in result

    def test_cicd(self):
        result = tokenize("Pipeline CI/CD avec Jenkins")
        assert "ci/cd" in result
        assert "jenkins" in result

    def test_sap_modules(self):
        result = tokenize("Consultant SAP S/4HANA FI/CO")
        assert "s/4hana" in result
        assert "fi/co" in result

    def test_spring_boot_compound(self):
        result = tokenize("Application Spring Boot microservices")
        assert "spring_boot" in result
        assert "microservices" in result

    def test_power_bi(self):
        result = tokenize("Tableaux de bord Power BI")
        assert "power_bi" in result

    def test_sap_with_dot(self):
        """SAP. with trailing dot should still match SAP."""
        # The word SAP itself isn't a tech token, but it should appear
        result = tokenize("SAP. implementation")
        assert "sap" in result


class TestStopwords:
    def test_french_stopwords_removed(self):
        result = tokenize("le développeur de la société est un expert")
        assert "le" not in result
        assert "de" not in result
        assert "la" not in result
        assert "est" not in result
        assert "un" not in result
        assert "developpeur" in result
        assert "expert" in result

    def test_english_stopwords_removed(self):
        result = tokenize("the developer is an expert in Java")
        assert "the" not in result
        assert "is" not in result
        assert "an" not in result
        assert "in" not in result
        assert "developer" in result
        assert "expert" in result
        assert "java" in result


class TestPunctuation:
    def test_punctuation_stripped(self):
        result = tokenize("Java, Spring Boot, et Oracle.")
        assert "java" in result
        assert "spring_boot" in result
        assert "oracle" in result
        # Commas and dots should not appear as separate tokens

    def test_parentheses(self):
        result = tokenize("développement (Java/Spring)")
        assert "java" in result
        assert "developpement" in result


class TestSingleCharRemoval:
    def test_single_chars_removed(self):
        result = tokenize("a b c Java d e")
        # a, b, c, d, e are single chars and should be removed
        assert "java" in result
        for tok in result:
            assert len(tok) > 1 or tok in ("c#",)  # c# is a tech token
