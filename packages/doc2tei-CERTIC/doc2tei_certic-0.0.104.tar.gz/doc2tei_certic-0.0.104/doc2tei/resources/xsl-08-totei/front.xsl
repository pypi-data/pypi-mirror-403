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
    
<xsl:output method="xml" encoding="UTF-8" indent="no"/>

<xsl:template match="*:p[starts-with(@text:style-name,'TEI_acknowledgment')][not(preceding-sibling::*:p[starts-with(@text:style-name,'TEI_acknowledgment')])]">
  <div type="ack">
    <p>
        <xsl:copy-of select="@rendition"/>
        <xsl:apply-templates/>
    </p>
    <xsl:for-each select="following-sibling::*:p[starts-with(@text:style-name,'TEI_acknowledgment')]">
      <p><xsl:apply-templates select="node()"/></p>
    </xsl:for-each>
  </div>
</xsl:template>
    
<xsl:template match="*:p[starts-with(@text:style-name,'TEI_dedication')][not(preceding-sibling::*:p[starts-with(@text:style-name,'TEI_dedication')])]">
    <div type="dedication">
        <p>
            <xsl:copy-of select="@rendition"/>
            <xsl:apply-templates/>
        </p>
        <xsl:for-each select="following-sibling::*:p[starts-with(@text:style-name,'TEI_dedication')]">
            <p><xsl:apply-templates select="node()"/></p>
        </xsl:for-each>
    </div>
</xsl:template>
     
<xsl:template match="*:p[starts-with(@text:style-name,'TEI_paragraph_lead')][not(preceding-sibling::*:p[starts-with(@text:style-name,'TEI_paragraph_lead')])]">
    <argument>
        <p>
            <xsl:copy-of select="@rendition"/>
            <xsl:apply-templates/>
        </p>
        <xsl:for-each select="following-sibling::*:p[starts-with(@text:style-name,'TEI_paragraph_lead')]">
            <p><xsl:apply-templates select="node()"/></p>
        </xsl:for-each>
    </argument>
</xsl:template>
    
<xsl:template match="*:p[starts-with(@text:style-name,'TEI_erratum')][not(preceding-sibling::*:p[starts-with(@text:style-name,'TEI_erratum')])]">
    <div type="correction">
        <p>
            <xsl:copy-of select="@rendition"/>
            <xsl:apply-templates/>
        </p>
        <xsl:for-each select="following-sibling::*:p[starts-with(@text:style-name,'TEI_erratum')]">
            <p><xsl:apply-templates select="node()"/></p>
        </xsl:for-each>
    </div>
</xsl:template>
    
<xsl:template match="*:p[starts-with(@text:style-name,'TEI_funder')]">
    <div type="funder">
        <p><xsl:apply-templates/></p>
    </div>
</xsl:template>

<xsl:template match="text:p[@text:style-name='TEI_partner']">
    <div type="sponsor">
        <p><xsl:apply-templates/></p>
    </div>
</xsl:template>
    
<xsl:template match="text:span[starts-with(@text:style-name,'TEI_fundername_inline')]|text:span[starts-with(@text:style-name,'TEI_funderref_inline')]">
    <name><xsl:apply-templates/></name>
</xsl:template>
    
<xsl:template match="*:p[starts-with(@text:style-name,'TEI_keywords')]">
    <xsl:variable name="currentLang" select="@xml:lang"/>
    <div type="keywords" xml:lang="{$currentLang}">
        <p><xsl:apply-templates/></p>
    </div>
</xsl:template>
    
<!-- Notes préliminaires -->
<xsl:template match="*:p[starts-with(@text:style-name,'TEI_note')]">
    <xsl:variable name="currentType" select="substring-after(@text:style-name,':')"/>
    <xsl:choose>
        <xsl:when test="not(preceding-sibling::*:p[starts-with(@text:style-name,'TEI_note') and substring-after(@text:style-name,':') = $currentType])">
            <note type="{$currentType}">
                <p>
                    <xsl:copy-of select="@rendition"/>
                    <xsl:apply-templates/>
                </p>
                <xsl:for-each select="following-sibling::*:p[starts-with(@text:style-name,'TEI_note') and substring-after(@text:style-name,':') = $currentType]">
                    <p>
                        <xsl:copy-of select="@rendition"/>
                        <xsl:apply-templates select="node()"/>
                    </p>
                </xsl:for-each>
            </note>
        </xsl:when>
        <xsl:otherwise/>
    </xsl:choose>
</xsl:template>      

<!-- Résumés -->
<xsl:template match="*:p[starts-with(@text:style-name,'TEI_abstract')]">
    <xsl:variable name="currentLang" select="@xml:lang"/>
    <xsl:choose>
        <xsl:when test="not(preceding-sibling::*:p[starts-with(@text:style-name,'TEI_abstract') and @xml:lang = $currentLang])">
            <div type="abstract" xml:lang="{$currentLang}">
                <p>
                    <xsl:copy-of select="@* except(@text:style-name)"/> 
                    <xsl:apply-templates/>
                </p>
                <xsl:for-each select="following-sibling::*:p[starts-with(@text:style-name,'TEI_abstract') and @xml:lang = $currentLang]">
                    <p>
                        <xsl:copy-of select="@* except(@text:style-name)"/>
                        <xsl:apply-templates select="node()"/>
                    </p>
                </xsl:for-each>
            </div>
        </xsl:when>
        <xsl:otherwise/>
    </xsl:choose>
<!--
<xsl:for-each-group select="//*:p[starts-with(@text:style-name,'TEI_abstract')]" group-by="@xml:lang">
    <div type="abstract">
        <xsl:copy-of select="@xml:lang"/>
        <xsl:for-each select="current-group()">
            <xsl:apply-templates select="." mode="front"/>
        </xsl:for-each>
    </div>
</xsl:for-each-group>
-->
</xsl:template>  
    
<!-- titlePage -->
<xsl:template match="text:h[@text:style-name='Title']">
    <p rend="title-main"><!-- rend="{@text:style-name}" -->
        <xsl:copy-of select="@xml:lang|@rendition"/>
        <xsl:apply-templates/>
    </p>
</xsl:template>
    
<xsl:template match="*:p[starts-with(@text:style-name,'TEI_aut')][@text:style-name!='TEI_authority_biography']">
    <p rend="{replace(replace(substring-after(@text:style-name,'TEI_'),':','-'),' ','-')}">
        <xsl:copy-of select="@xml:lang|@rendition"/>
        <xsl:apply-templates/>
    </p>
</xsl:template>

<xsl:template match="*:p[starts-with(@text:style-name,'TEI_author:')]">
    <xsl:choose>
        <xsl:when test="ancestor::*:div[@type='review']">
            <p rend="{replace(replace(substring-after(@text:style-name,'TEI_'),':','-'),' ','-')}">
                <xsl:copy-of select="@xml:lang|@rendition"/>
                <xsl:apply-templates/>
            </p>
            <!-- ce if pour ne pas créer d'élément biographie pour les auteurs qui n'en ont pas -->
            <xsl:if test="following-sibling::*:p[@text:style-name='TEI_authority_biography']
                        [preceding-sibling::*[starts-with(@text:style-name,'TEI_author:')][1] 
                        [count(preceding-sibling::*) = count(current()/preceding-sibling::*)]]">   
                <p rend='authority_biography'> 
                    <!-- les 3 lignes suivantes pour gérer plusieurs auteurs par recension avec bio : cela va chercher la bio following sibling de chaque auteur, en arrêtant la recherche au prochain auteur -->
                    <xsl:for-each select="following-sibling::*:p[@text:style-name='TEI_authority_biography']
                                        [not(preceding-sibling::*[starts-with(@text:style-name,'TEI_author:')]
                                        [count(preceding-sibling::*) > count(current()/preceding-sibling::*)])]">                   
                        <xsl:apply-templates/>
                        <xsl:if test="position() != last()">
                            <lb/>
                        </xsl:if>
                    </xsl:for-each>
                </p> 
            </xsl:if>
        </xsl:when>
        <xsl:otherwise>
            <p rend="{replace(replace(substring-after(@text:style-name,'TEI_'),':','-'),' ','-')}">
                <xsl:copy-of select="@xml:lang|@rendition"/>
                <xsl:apply-templates/>
            </p> 
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>
    
<xsl:template match="*:p[starts-with(@text:style-name,'TEI_editor')]">
    <p rend="{replace(substring-after(@text:style-name,'TEI_'),':','-')}">
        <xsl:copy-of select="@xml:lang|@rendition"/>
        <xsl:apply-templates/>
    </p>
</xsl:template>
    
<xsl:template match="*:p[starts-with(@text:style-name,'TEI_title')]">
    <p rend="{replace(substring-after(@text:style-name,'TEI_'),':','-')}">
        <xsl:copy-of select="@xml:lang|@rendition"/>
        <xsl:apply-templates/>
    </p>
</xsl:template>
    
<xsl:template match="text:span[starts-with(@text:style-name,'TEI_author-inline:')]|text:span[starts-with(@text:style-name,'TEI_editor-inline:')]">
    <xsl:apply-templates/>
</xsl:template>
    
<xsl:template match="text:span[starts-with(@text:style-name,'TEI_affiliation-inline')]">
    <affiliation><xsl:apply-templates/></affiliation>
</xsl:template>
    
<xsl:template match="text:span[@text:style-name='TEI_mail-inline']">
    <email><xsl:apply-templates/></email>
</xsl:template>

<!-- Recensions -->
<xsl:template match="text:p[@text:style-name='TEI_reviewed_reference']">
    <listBibl><xsl:apply-templates select="." mode="review"/></listBibl>
</xsl:template>
    
<xsl:template match="text:p[@text:style-name='TEI_reviewed_reference']|text:h[@subtype='review']" mode="review">
    <bibl type="display"><xsl:apply-templates/></bibl>
    <bibl type="semantic"><xsl:apply-templates select="descendant::text:span[starts-with(@text:style-name,'TEI_reviewed') and ends-with(@text:style-name,'inline')]" mode="reviewSemantic"/></bibl>
</xsl:template>
    
<xsl:template match="text:span[starts-with(@text:style-name,'TEI_reviewed') and ends-with(@text:style-name,'inline')]">
    <xsl:apply-templates/>
</xsl:template>
    
<xsl:template match="text:span[@text:style-name='TEI_reviewed_author-inline']" mode="reviewSemantic">
    <author>
        <persName>
            <xsl:variable name="name" select="normalize-space(.)"/>
            <xsl:variable name="tokens" select="tokenize($name, ' ')"/>
            <xsl:variable name="surname" select="$tokens[last()]"/>
            
            <forename><xsl:value-of select="normalize-space(substring-before($name, $surname))"/></forename>
            <surname><xsl:value-of select="$surname"/></surname>
        </persName>
    </author>
</xsl:template>
    
<xsl:template match="text:span[@text:style-name='TEI_reviewed_title-inline']" mode="reviewSemantic">
    <title><xsl:apply-templates select=".//text()"/></title>
</xsl:template>
        
<xsl:template match="text:span[@text:style-name='TEI_reviewed_date-inline']" mode="reviewSemantic">
    <date><xsl:apply-templates select=".//text()"/></date>
</xsl:template>
    
<!-- archéo -->
<xsl:template match="*:p[starts-with(@text:style-name,'TEI_archeoART')][not(preceding-sibling::*:p[starts-with(@text:style-name,'TEI_archeoART')])]">
  <div type="archeo">
    <p rend="{concat('archeo_',substring-after(@text:style-name,'TEI_archeoART_'))}"><xsl:apply-templates/></p>
    <xsl:for-each select="following-sibling::*:p[starts-with(@text:style-name,'TEI_archeoART')]">
      <p rend="{concat('archeo_',substring-after(@text:style-name,'TEI_archeoART_'))}"><xsl:apply-templates select="node()"/></p>
    </xsl:for-each>
  </div>
</xsl:template>
    
<!-- suppression -->
<xsl:template match="*:p[starts-with(@text:style-name,'TEI_acknowledgment')][preceding-sibling::*:p[starts-with(@text:style-name,'TEI_acknowledgment')]]"/>
<xsl:template match="*:p[starts-with(@text:style-name,'TEI_dedication')][preceding-sibling::*:p[starts-with(@text:style-name,'TEI_dedication')]]"/>
<xsl:template match="*:p[starts-with(@text:style-name,'TEI_paragraph_lead')][preceding-sibling::*:p[starts-with(@text:style-name,'TEI_paragraph_lead')]]"/>
<xsl:template match="*:p[starts-with(@text:style-name,'TEI_erratum')][preceding-sibling::*:p[starts-with(@text:style-name,'TEI_erratum')]]"/>
<xsl:template match="*:p[starts-with(@text:style-name,'TEI_archeoART')][preceding-sibling::*:p[starts-with(@text:style-name,'TEI_archeoART')]]"/>

</xsl:stylesheet>