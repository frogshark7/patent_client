import pytest

from . import (
    Patent,
    PatentBiblio,
    PublicSearchDocument,
    PublishedApplication,
    PublishedApplicationBiblio,
)


class TestPatents:
    @pytest.mark.asyncio
    async def test_simple_lookup(self):
        app = await PublicSearchDocument.objects.get(patent_number="6103599")
        assert app.appl_id == "09089931"
        assert app.guid == "US-6103599-A"
        assert app.patent_title == "Planarizing technique for multilayered substrates"

    @pytest.mark.asyncio
    async def test_tennis_patents(self):
        tennis_patents = Patent.objects.filter(title="tennis", assignee_name="wilson")
        assert await tennis_patents.count() > 10

    @pytest.mark.asyncio
    async def test_fetch_patent(self):
        pat = await Patent.objects.get(6095661)
        assert pat.patent_title == "Method and apparatus for an L.E.D. flashlight"
        assert len(pat.abstract) == 1543

    @pytest.mark.asyncio
    async def test_government_interest(self):
        pat = await Patent.objects.get(11555621)
        assert pat.document.government_interest is not None

    @pytest.mark.asyncio
    async def test_claims(self):
        pat = await Patent.objects.get(6095661)
        assert len(pat.claims) == 52
        assert pat.claims[0].number == 1
        assert len(pat.claims[0].text) == 1269
        assert len(pat.claims[0].limitations) == 5
        assert pat.claims[30].number == 31
        assert len(pat.claims[30].text) == 461
        assert len(pat.claims[30].limitations) == 4
        assert not pat.claims[30].dependent
        assert pat.claims[30].independent
        assert pat.claims[30].depends_on == list()
        assert pat.claims[31].dependent
        assert not pat.claims[31].independent
        assert pat.claims[31].depends_on == [
            31,
        ]

    @pytest.mark.asyncio
    async def test_us8645300(self):
        pat_no = 8645300
        pat = await Patent.objects.get(pat_no)
        assert pat.patent_title == "System and method for intent data processing"

    @pytest.mark.asyncio
    async def test_search_classification(self):
        query = '"B60N2/5628".CPC. AND @APD>="20210101"<=20210107'
        results = Patent.objects.filter(query=query)
        assert await results.count() >= 1
        app = await results.first()
        assert app.publication_number == "11554698"

    @pytest.mark.asyncio
    async def test_can_fetch_reissue_applications(self):
        pat_no = "RE43633"
        pat = await Patent.objects.get(pat_no)
        assert (
            pat.patent_title
            == "System and method for linking streams of multimedia data to reference material for display"
        )
        assert pat.claims[0].text[:25] == "1. .[.A system for linkin"

    @pytest.mark.asyncio
    async def test_can_get_field_of_search(self):
        pat_no = "9140110"
        pat = await Patent.objects.get(pat_no)
        assert len(pat.field_of_search_us) >= 6
        pat_no = "8832265"
        pat = await Patent.objects.get(pat_no)
        assert len(pat.field_of_search_us) == 7

    @pytest.mark.asyncio
    async def test_handles_disclaimers(self):
        """Some patents have notice markers on the issue date regarding statutory disclaimers"""
        pat = await Patent.objects.get("5439055")
        assert pat.publication_date.isoformat() == "1995-08-08"

    @pytest.mark.asyncio
    async def test_handles_claims_for_US6460631(self):
        pat = await Patent.objects.get(6460631)
        for claim in pat.claims:
            pass
        assert True

    @pytest.mark.asyncio
    async def test_handles_search_without_results(self):
        query = Patent.objects.filter(query='"379/56".CCLS. AND @APD>=19700101<=19950928')
        assert await query.count() == 0

    @pytest.mark.asyncio
    async def test_can_get_forward_references(self):
        pat = await Patent.objects.get(6103599)
        forward_refs = await (pat.forward_citations.count())
        
        assert forward_refs >= 100

    @pytest.mark.asyncio
    async def test_classifications_with_foreign_priority_data(self):
        pat = await Patent.objects.get(7752445)
        assert len(pat.us_class_issued) == 6
        assert pat.foreign_priority[0].app_number == "2004-052835"

    @pytest.mark.asyncio
    async def test_can_get_design_patents(self):
        pat = await Patent.objects.get("D645062")
        assert pat.patent_title == "Gripping arm"
        assert pat.appl_id == "29380046"

    @pytest.mark.asyncio
    async def test_search_that_has_single_patent(self):
        result = Patent.objects.filter(title="tennis", issue_date="2010-01-01->2010-02-27")
        assert await result.count() == 1
        obj = await result.first()
        assert obj.publication_number == "7658211"
        assert obj.patent_title == "Tennis ball recharging apparatus method"

    @pytest.mark.asyncio
    async def test_can_get_images(self, tmp_path):
        pat = await Patent.objects.get("6103599")
        path = await pat.download_images(path=tmp_path)
        assert path == tmp_path / "US-6103599-A.pdf"
        assert path.exists()


class TestPublishedApplicationFullTextAsync:
    @pytest.mark.asyncio
    async def test_fetch_publication(self):
        pub_no = 20_160_009_839
        pub = await PublishedApplication.objects.get(pub_no)
        assert (
            pub.patent_title
            == "POLYMER PRODUCTS AND MULTI-STAGE POLYMERIZATION PROCESSES FOR THE PRODUCTION THEREOF"
        )
        assert len(pub.abstract) == 651

    @pytest.mark.asyncio
    async def test_publication_claims(self):
        pub_no = 20_160_009_839
        pub = await PublishedApplication.objects.get(pub_no)
        assert len(pub.claims) == 25
        # Test Claim 1
        claim_1 = pub.claims[0]
        assert claim_1.number == 1
        assert len(claim_1.text) == 487
        assert len(claim_1.limitations) == 3
        assert claim_1.independent
        # Test Dependent Claim 2
        claim_2 = pub.claims[1]
        assert claim_2.number == 2
        assert claim_2.dependent

    @pytest.mark.asyncio
    async def test_us_pub_20170370151(self):
        pub_no = 20_170_370_151
        pub = await PublishedApplication.objects.get(pub_no)
        for i in range(6):
            assert pub.claims[i].text == f"{i + 1}. (canceled)"
        assert (
            "A system to control directional drilling in borehole drilling for"
            in pub.claims[6].text
        )

    @pytest.mark.asyncio
    async def test_search_classification(self):
        query = '"166/308.1".CCLS. AND @APD>=20150101<=20210101'
        results = PublishedApplicationBiblio.objects.filter(query=query)
        count = await results.count()
        assert count >= 35
        counter = 0
        async for _ in results:
            counter += 1
        assert counter == count

    @pytest.mark.asyncio
    async def test_nonstandard_claim_format(self):
        obj = await PublishedApplication.objects.get("20170260839")
        assert obj.claims[0].text[:39] == "1. A method of well ranging comprising:"

    @pytest.mark.skip("This test is too slow")
    @pytest.mark.asyncio
    async def test_can_get_images(self, tmp_path):
        pat = await PublishedApplication.objects.get("20090150362")
        await pat.adownload_images(path=tmp_path)
        assert (tmp_path / "US-20090150362-A1.pdf").exists()

    @pytest.mark.asyncio
    async def test_pages(self):
        pats = PatentBiblio.objects.filter(title="system").limit(525)
        old_p = None
        counter = 0
        async for p in pats:
            counter += 1
            assert p != old_p
        assert counter >= 525
