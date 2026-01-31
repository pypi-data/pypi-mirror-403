<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
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
  xmlns="http://www.tei-c.org/ns/1.0"
  exclude-result-prefixes="#all">
    
<xsl:output method="xml" encoding="UTF-8" indent="no"/>

<!-- ajouter LICENCE -->
<!-- voir README.md pour la description des traitements XSL -->
    
<xsl:variable name="source">
    <xsl:value-of select="//meta:user-defined[@meta:name='source']"/>
</xsl:variable> 

<!-- front div type='titlePage', abstracts, erratum, notes préliminaires, métadonnées recensions, dédicace, remerciements, chapô, épigraphe -->

<xsl:variable name="titlePageNodes" as="node()*">
    <xsl:sequence select="//text:p[starts-with(@text:style-name,'TEI_author')][not(preceding::meta:user-defined[@meta:name='typez39']/text()='review') and not(ancestor::*:div[@type='review'])] | 
                          //text:p[starts-with(@text:style-name,'TEI_editor')] | 
                          //text:p[starts-with(@text:style-name,'TEI_title')] | 
                          //text:h[@text:style-name='Title']"/>
</xsl:variable>
    <!--[@text:style-name!='TEI_authority_biography']-->

<xsl:variable name="firstStandardPara" as="node()*">
    <xsl:sequence select="(//*:text//text:p[@text:style-name='Standard'])[1]"/>
</xsl:variable>
    
<xsl:variable name="firstPara" as="node()*">
    <xsl:choose>
        <xsl:when test="not(//*:text//text:p[@text:style-name='Standard']) and //*:text//*:sp[@rend='question']">
            <xsl:sequence select="(//*:text//*:sp[@rend='question'])[1]"/>
        </xsl:when>
        <xsl:when test="//*:text//*:sp[@rend='question'][1][following::text:p=$firstStandardPara]">
            <xsl:sequence select="(//*:text//*:sp[@rend='question'])[1]"/>
        </xsl:when>
        <xsl:when test="//*:cit[@type='linguistic'][1][following::text:p=$firstStandardPara]">
            <xsl:sequence select="//*:cit[@type='linguistic'][1][following::text:p=$firstStandardPara]"/>
        </xsl:when>
        <xsl:when test="//*:cit[1][following::text:p=$firstStandardPara]|//*:p[@text:style-name='TEI_quote'][1][following::text:p=$firstStandardPara]">
            <xsl:sequence select="//*:cit[1][following::text:p=$firstStandardPara]|//*:p[@text:style-name='TEI_quote'][1][following::text:p=$firstStandardPara]"/>
        </xsl:when>
        <xsl:otherwise>
            <xsl:sequence select="(//*:text//text:p[@text:style-name='Standard'])[1]"/>
        </xsl:otherwise>
    </xsl:choose>
</xsl:variable>
    
<xsl:variable name="frontNodes" as="node()*">
    <!-- syntaxe déclarative -->
<!--
    <xsl:sequence select="//text:p[starts-with(@text:style-name,'TEI_acknowledgment')] | 
                          //text:p[starts-with(@text:style-name,'TEI_dedication')] | 
                          //text:p[starts-with(@text:style-name,'TEI_note:')] | 
                          //text:p[starts-with(@text:style-name,'TEI_paragraph_lead')] | 
                          //text:p[starts-with(@text:style-name,'TEI_abstract')] | 
                          //text:p[starts-with(@text:style-name,'TEI_keywords')] | 
                          //text:p[starts-with(@text:style-name,'TEI_erratum')] | 
                          //text:p[starts-with(@text:style-name,'TEI_funder')] | 
                          //text:p[starts-with(@text:style-name,'TEI_reviewed_reference')] | 
                          //text:p[starts-with(@text:style-name,'TEI_epigraph') and not(parent::*:div[contains(@type,'section')])] | 
                          //text:p[starts-with(@text:style-name,'TEI_bibl_reference') and not(ancestor::*:div[@type]) and not(ancestor::*:note)]"/>
-->
<!--  tous les éléments qui précèdent le premier paragraphe 'Standard' (et ne sont pas des éléments de titlePageNodes)  -->
    <xsl:sequence select="$firstPara/preceding::text:*[not(ancestor::text:note) and not(ancestor::*:div) and not(ancestor::*:figure) and not(self::text:note) and not(self::text:span) and not(self::text:a) and not(self::text:line-break)] except ($titlePageNodes)"/>
</xsl:variable>

<!--
<xsl:variable name="bodyNodesException" as="node()*">
    <xsl:sequence select="//text:p[@text:style-name='TEI_authority_biography']"/>
</xsl:variable>
-->
    
<xsl:variable name="backNodes" as="node()*">
    <xsl:sequence select="//*:div[@type='appendix'] | //*:div[@type='bibliography']"/>
</xsl:variable>
    
<xsl:template match="@*|node()">
  <xsl:copy>
    <xsl:apply-templates select="@*|node()"/>
  </xsl:copy>
</xsl:template>

<xsl:template match="/">
<TEI change="commons_edition">
    <xsl:apply-templates select="//office:meta|//office:automatic-styles"/>
    <teiHeader/>
    <text xml:id="text">
      <xsl:attribute name="type" select="//meta:user-defined[@meta:name='typez39']"/>
      <front>
          <div type="titlePage">
              <xsl:apply-templates select="$titlePageNodes"/>
              <xsl:if test="//text:h[@text:outline-level='0' and @subtype='review']">
                  <p rend="title-main">
                      <xsl:apply-templates select="//text:h[@text:outline-level='0' and @subtype='review']//text:span[@text:style-name='TEI_reviewed_title-inline']"/>
                  </p>
              </xsl:if>
          </div>
          <xsl:apply-templates select="$frontNodes"/>
      </front>
<!-- à reprendre : voir fichier signata 1410-->
      <body>
          <xsl:apply-templates select="//text/* except ($titlePageNodes | $frontNodes | $backNodes)"/> <!-- $bodyNodesException | -->
      </body>
<!-- back : bibliographie, annexe, bio auteurs -->
        <xsl:if test="//*:div[@type='bibliography' or @type='appendix'] or (//*:p[@text:style-name='TEI_authority_biography'])">
            <!--      and $source='Metopes'       -->
            <back>
                <xsl:apply-templates select="//*:div[@type='bibliography']"/>
                <xsl:apply-templates select="//*:div[@type='appendix']"/>
                <xsl:if test="//*:p[@text:style-name='TEI_authority_biography']">
                    <div type="biographies">
                        <xsl:apply-templates select="//*:p[starts-with(@text:style-name,'TEI_author:')]|//*:p[starts-with(@text:style-name,'TEI_editor:')]|//*:p[@text:style-name='TEI_authority_biography']"/>
                    </div>
                </xsl:if>
            </back>
        </xsl:if>
    </text>
</TEI>
</xsl:template>
    
<xsl:template match="*:div[@type='review']/*:div[starts-with(@type,'section')]">
    <xsl:choose>
        <xsl:when test="child::text:p[@text:style-name='TEI_section_author']">
            <div>
                <xsl:copy-of select="@*"/>
                <xsl:apply-templates select="* except (text:p[@text:style-name='TEI_section_author'] | text:p[starts-with(@text:style-name,'TEI_author')])"/>
            </div>
            <div type="sec_authority">
                <xsl:apply-templates select="text:p[@text:style-name='TEI_section_author'] | text:p[starts-with(@text:style-name,'TEI_author')]"/>
            </div>
        </xsl:when>
        <xsl:otherwise><xsl:copy-of select="."/></xsl:otherwise>
    </xsl:choose>
</xsl:template>
    
</xsl:stylesheet>