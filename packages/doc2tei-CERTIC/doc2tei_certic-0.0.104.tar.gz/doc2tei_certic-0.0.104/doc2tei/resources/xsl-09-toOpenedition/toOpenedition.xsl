<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
        xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
		xmlns="http://www.tei-c.org/ns/1.0"
        xmlns:tei="http://www.tei-c.org/ns/1.0"
		xmlns:xinclude="http://www.w3.org/2001/XInclude"
		xmlns:mets="http://www.loc.gov/METS/"
   		xmlns:marcrel="http://www.loc.gov/loc.terms/relators"
   		xmlns:mods="http://www.loc.gov/mods/v3"
		xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
  xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
  xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
  xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0"
  xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" 
  xmlns:chart="urn:oasis:names:tc:opendocument:xmlns:chart:1.0" 
  xmlns:dr3d="urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0" 
  xmlns:math="http://www.w3.org/1998/Math/MathML" 
  xmlns:form="urn:oasis:names:tc:opendocument:xmlns:form:1.0" 
  xmlns:script="urn:oasis:names:tc:opendocument:xmlns:script:1.0" 
  xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0" 
  xmlns:ooo="http://openoffice.org/2004/office" 
  xmlns:ooow="http://openoffice.org/2004/writer" 
  xmlns:oooc="http://openoffice.org/2004/calc" 
  xmlns:dom="http://www.w3.org/2001/xml-events" 
  xmlns:xforms="http://www.w3.org/2002/xforms" 
  xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
  xmlns:rpt="http://openoffice.org/2005/report" 
  xmlns:of="urn:oasis:names:tc:opendocument:xmlns:of:1.2" 
  xmlns:xhtml="http://www.w3.org/1999/xhtml" 
  xmlns:grddl="http://www.w3.org/2003/g/data-view#" 
  xmlns:officeooo="http://openoffice.org/2009/office" 
  xmlns:tableooo="http://openoffice.org/2009/table" 
  xmlns:drawooo="http://openoffice.org/2010/draw" 
  xmlns:calcext="urn:org:documentfoundation:names:experimental:calc:xmlns:calcext:1.0" 
  xmlns:loext="urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0" 
  xmlns:field="urn:openoffice:names:experimental:ooo-ms-interop:xmlns:field:1.0" 
  xmlns:formx="urn:openoffice:names:experimental:ooxml-odf-interop:xmlns:form:1.0" 
  xmlns:css3t="http://www.w3.org/TR/css3-text/"
  exclude-result-prefixes="office style text table draw fo xlink dc meta number svg chart  dr3d math form script config ooo ooow oooc dom xforms xsd xsi rpt of xhtml grddl officeooo tableooo drawooo calcext loext field formx css3t tei mets mods marcrel xinclude">

<!-- exclude-result-prefixes="tei"-->

<xsl:output method="xml" encoding="UTF-8" indent="no"/>

<!-- ajouter LICENCE -->
<!-- voir README.md pour la description des traitements XSL -->    

<xsl:template match="@*|node()">
  <xsl:copy>
    <xsl:apply-templates select="@*|node()"/>
  </xsl:copy>
</xsl:template>
    
<!-- traitement des différences entre TEI Commons expression Métopes et TEI Commons expression OpenEdition : 
• Métadonnées OpenEdition 
    - titres avec enrichissements ;
    - sourceDesc/biblStruct ;
    - code langue sur 2 caractères
    - notes biographiques dans le teiHeader ;
• Spec Métopes converties :
    - suppression des titres de sections bibliographiques et annexes ;
    – passage de x à 1 affiliation (affililation/orgName) ;
    - liste tirets converties en listes avec puces disc ;
    - auteur de section : paragraphe non nméroté ferré à droite ;
    - suppression type de document, surcharges, des entrées d'index, des éléments foreign ;
    - citations de théâtre (cit/quote/sp) et poésie (cit/quote/lg) ramenées à théâtre (sp) et poésie (lg)
-->

<!-- ## TEIHEADER ## -->
<xsl:template match="tei:titleStmt">
    <titleStmt>
        <xsl:for-each select="following::tei:p[starts-with(@rend,'title-') and parent::tei:div[@type='titlePage']]">
            <title type="{substring-after(@rend,'title-')}">
                <xsl:if test="@xml:lang">
                    <xsl:copy-of select="@xml:lang"/>
                </xsl:if>
                <xsl:if test="@rendition">
                    <xsl:copy-of select="@rendition"/>
                </xsl:if>
                <xsl:apply-templates/>
            </title>
        </xsl:for-each>
        <xsl:apply-templates select="child::tei:author|child::tei:editor|child::tei:funder"/>
    </titleStmt>
</xsl:template>
    
<xsl:template match="tei:affiliation[ancestor::tei:teiHeader]">
    <xsl:choose>
        <!-- suppression des affiliations qui ne sont pas les premières pour un bloc d'autorité… -->
        <xsl:when test="preceding-sibling::*[1]/local-name()='affiliation'"/>
        <!-- méthode par lien affiliation/ref[@type='affiliation'] -->
        <xsl:when test="child::tei:ref[@type='affiliation']">
            <xsl:variable name="affID"><xsl:value-of select="substring-after(child::tei:ref[@type='affiliation']/@target,'#')"/></xsl:variable>
            <affiliation>
                <orgName>
                    <xsl:value-of select="following::tei:affiliation[@xml:id=$affID]"/>
                    <xsl:if test="following-sibling::tei:affiliation">
                        <xsl:for-each select="following-sibling::tei:affiliation">
                            <xsl:variable name="affID"><xsl:value-of select="substring-after(child::tei:ref[@type='affiliation']/@target,'#')"/></xsl:variable>
                            <xsl:text>, </xsl:text><xsl:value-of select="following::tei:affiliation[@xml:id=$affID]"/>
                        </xsl:for-each>
                    </xsl:if>
                </orgName>
            </affiliation>
        </xsl:when>
        <!-- méthode "plateforme" affiliation/orgName/text() -->
        <xsl:otherwise>
            <affiliation>
                <orgName>
<!--
                    <xsl:if test="child::tei:orgName/text() = following::tei:p[@rend='authority_affiliation' and @rendition='#rtl']/text()">
                        <xsl:attribute name="rendition">#rtl</xsl:attribute>
                    </xsl:if>
-->
                    <xsl:copy-of select="child::tei:orgName/node()"/>
                    <xsl:if test="following-sibling::tei:affiliation">
                        <xsl:text>, </xsl:text><xsl:copy-of select="following-sibling::tei:affiliation/tei:orgName/node()"/>
                    </xsl:if>
                </orgName>
            </affiliation>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>
    
<xsl:template match="tei:orgName">
    <xsl:variable name="aff" select="text()"/>
    <xsl:choose>
        <xsl:when test="$aff = following::tei:p[@rend='authority_affiliation']/text() ">
<!--     $aff = following::tei:p[@rend='authority_affiliation' and @rendition='#rtl']/text()        -->
            <orgName><!-- rendition="#rtl" -->
                <xsl:copy-of select="@*"/>
                <xsl:apply-templates/>
            </orgName>
        </xsl:when>
        <xsl:otherwise>
            <xsl:copy>
                <xsl:apply-templates select="@*|node()"/>
            </xsl:copy>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>
    
<xsl:template match="tei:ref[@type='biography']">
    <xsl:variable name="bioId" select="substring-after(@target,'#')"/>
    <note type="biography">
        <xsl:copy-of select="following::tei:div[@type='biography' and @xml:id=$bioId]/node()"/>
    </note>
</xsl:template>
    
<xsl:template match="tei:publicationStmt">
    <publicationStmt>
        <distributor>OpenEdition</distributor>
        <xsl:if test="child::tei:date[@type='received'] !='' ">
            <xsl:copy-of select="child::tei:date[@type='received']"/>
        </xsl:if>
        <xsl:if test="child::tei:date[@type='accepted'] !='' ">
            <xsl:copy-of select="child::tei:date[@type='accepted']"/>
        </xsl:if>
        <xsl:if test="//tei:ab[@subtype='HTML']/tei:bibl/tei:idno[@type='documentnumber'] !=''">
            <xsl:copy-of select="//tei:ab[@subtype='HTML']/tei:bibl/tei:idno[@type='documentnumber']"/>
        </xsl:if>
<!--    <availability>
            <licence></licence>
        </availability>-->
    </publicationStmt>
    <sourceDesc>
        <xsl:choose>
            <xsl:when test="//tei:ab[@type='book']//tei:biblScope[@unit='page']/@from != ''">
                <biblStruct>
                    <monogr>
                        <imprint>
                            <biblScope unit="page">
                                <xsl:value-of select="//tei:ab[@type='book']//tei:biblScope[@unit='page']/@from"/>
                                <xsl:if test="//tei:ab[@type='book']//tei:biblScope[@unit='page']/@to != ''">
                                    <xsl:value-of select="concat('-',//tei:ab[@type='book']//tei:biblScope[@unit='page']/@to)"/>
                                </xsl:if>
                            </biblScope>
                        </imprint>
                    </monogr>
                </biblStruct>
            </xsl:when>
            <xsl:otherwise>
                <p>Circé</p>
            </xsl:otherwise>
        </xsl:choose>
    </sourceDesc>
</xsl:template>
    
<xsl:template match="tei:tagsDecl">
    <tagsDecl>
        <xsl:if test="child::tei:rendition[@xml:id='list-ndash'] and not(child::tei:rendition[@xml:id='list-ndash'])">
            <rendition scheme="css" xml:id="list-disc">list-style-type:disc;</rendition>
        </xsl:if>
        <xsl:if test="following::tei:bibl[@type='sec_authority']">
            <rendition scheme="css" xml:id="end">text-align:end;</rendition>
        </xsl:if>
        <xsl:apply-templates/>
    </tagsDecl>
</xsl:template>
    
<xsl:template match="tei:language">
    <language>
        <xsl:attribute name="ident">
            <xsl:choose>
                <xsl:when test="contains(@ident,'-')">
                    <xsl:value-of select="substring-before(@ident,'-')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="@ident"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:attribute>
    </language>
</xsl:template>

<xsl:template match="@change"/>
<xsl:template match="tei:editorialDecl"/>
<xsl:template match="tei:ab"/>
<xsl:template match="tei:sourceDesc"/>
<xsl:template match="tei:funder[not(child::tei:*[@type='funder_registry'])]"/>

<!-- ## TEXT ## -->
<xsl:template match="tei:text">
    <xsl:copy>
        <xsl:apply-templates select="@*[name() != 'type']"/>
        <xsl:apply-templates select="node()"/>
  </xsl:copy>
</xsl:template>
    
<!-- ## FRONT ## -->
<xsl:template match="tei:div[@type='titlePage']"/>
<xsl:template match="tei:div[@type='keywords']"/>

<!-- ## BODY ## -->
<xsl:template match="tei:cit[descendant::tei:lg]">
    <xsl:apply-templates select="descendant::tei:lg"/>
</xsl:template>
    
<xsl:template match="tei:cit[(descendant::tei:sp)]">
<!--   or (child::tei:quote[child::tei:stage])  -->
    <xsl:apply-templates select="descendant::tei:sp|tei:quote/tei:stage"/>
</xsl:template>
    
<xsl:template match="tei:sp[not(ancestor::tei:cit)]">
    <xsl:choose>
        <xsl:when test="child::tei:bibl">
            <sp>
                <xsl:copy-of select="@*"/>
                <xsl:apply-templates select="child::tei:* except(tei:bibl)"/>
            </sp>
                <xsl:apply-templates select="tei:bibl"/>
        </xsl:when>
        <xsl:otherwise>
            <sp>
                <xsl:copy-of select="@*"/>
                <xsl:apply-templates/>
            </sp>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>
    
<xsl:template match="tei:cell">
    <xsl:copy>
        <xsl:apply-templates select="@*[name() != 'rendition']"/>
        <xsl:attribute name="rendition">
        <xsl:choose>
            <xsl:when test="count(child::tei:p) = 1 and child::tei:p[@rendition]">
                <xsl:value-of select="concat(./@rendition,' ', child::tei:p/@rendition)"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:copy-of select="@rendition"/>
            </xsl:otherwise>
        </xsl:choose>
        </xsl:attribute>
        <xsl:if test="count(child::tei:p) = 1 and child::tei:p[@xml:id]">
            <xsl:attribute name="xml:id" select="child::tei:p/@xml:id"/>
        </xsl:if>
        <xsl:if test="count(child::tei:p) = 1 and child::tei:p[@xml:lang]">
            <xsl:attribute name="xml:lang" select="child::tei:p/@xml:lang"/>
        </xsl:if>
        <xsl:apply-templates select="node()"/>
    </xsl:copy>
</xsl:template>
    
<xsl:template match="tei:p[parent::tei:cell]">
    <xsl:choose>
        <xsl:when test="count(../*) = 1 and @xml:lang">
            <xsl:apply-templates/>
        </xsl:when>
        <xsl:when test="count(../*) = 1 and @xml:id">
<!--            <anchor xml:id="{@xml:id}"/>-->
            <xsl:apply-templates/>
        </xsl:when>
        <xsl:otherwise>
            <xsl:copy>
                <xsl:apply-templates select="@*|node()"/>
          </xsl:copy>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>
    
<xsl:template match="tei:p[starts-with(@rend,'unknownstyle:')]">
  <xsl:copy>
    <xsl:apply-templates select="@*[name() != 'rend']"/>
    <xsl:apply-templates select="node()"/>
  </xsl:copy>
</xsl:template>
    
<xsl:template match="tei:p[starts-with(@rend,'TEI_local')]">
	<xsl:copy>
		<xsl:apply-templates select="@*[name() != 'rend']"/>
		<xsl:apply-templates select="node()"/>
	</xsl:copy>
</xsl:template>
    
<xsl:template match="tei:index"/>

<xsl:template match="tei:foreign">
   <xsl:apply-templates/>
</xsl:template>
    
<xsl:template match="tei:floatingText">
    <floatingText>
        <xsl:copy-of select="@* except(@type)"/>
        <xsl:apply-templates/>
    </floatingText>
</xsl:template>
    
<xsl:template match="tei:list[@rendition='#list-ndash']">
    <list>
        <xsl:copy-of select="@*"/>
        <xsl:attribute name="rendition">#list-disc</xsl:attribute>
        <xsl:apply-templates/>
    </list>
</xsl:template>
    
<xsl:template match="tei:bibl[@type='sec_authority']">
    <p rendition="#end">
        <xsl:apply-templates select="descendant::text()|descendant::tei:hi"/>
    </p>
</xsl:template>  
    
<!-- ## TYPO ## -->
<xsl:template match="tei:hi[starts-with(@rend,'TEI_local')]"> 
    <xsl:apply-templates select="node()"/>
</xsl:template>
    
<!-- ## BACK ## -->
<xsl:template match="tei:head[parent::tei:div[@type='bibliography']]|tei:head[parent::tei:div[@type='appendix']]"/>
    
<xsl:template match="tei:div[@type='biographies']"/>   

</xsl:stylesheet>