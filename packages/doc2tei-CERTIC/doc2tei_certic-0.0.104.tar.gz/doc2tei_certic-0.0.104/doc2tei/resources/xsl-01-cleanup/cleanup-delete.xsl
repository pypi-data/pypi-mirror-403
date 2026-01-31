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
  exclude-result-prefixes="formx config of svg dr3d calcext loext form field script chart">
    

<!-- données traitement de texte -->
<xsl:template match="office:settings"/>
<xsl:template match="office:scripts"/>
<xsl:template match="office:font-face-decls"/>
<xsl:template match="office:styles"/>
<xsl:template match="office:master-styles"/>
<xsl:template match="office:text/text:sequence-decls"/>
<xsl:template match="office:forms"/>

<!-- caractères de saut -->
<xsl:template match="text:soft-page-break"/>

<!-- This element shall be used to represent the second and all following “ “ (U+0020, SPACE) characters in a sequence of “ “ (U+0020, SPACE) characters. -->
<xsl:template match="text:s">
    <xsl:variable name="spaceNb" select="@text:c"/>
    <xsl:choose>
        <xsl:when test="local-name(preceding-sibling::node()[1])='frame'">
            <xsl:text> </xsl:text>
        </xsl:when>
        <xsl:when test="ancestor::text:p[@text:style-name='TEI_5f_code_3a_xml']">
            <xsl:for-each select="1 to $spaceNb"><xsl:text xml:space="preserve"> </xsl:text></xsl:for-each>
        </xsl:when>
        <xsl:otherwise/>
    </xsl:choose>
</xsl:template>

<!-- ancres par défaut | bookmarks -->
<!--<xsl:template match="text:bookmark[starts-with(@text:name,'_')]"/>-->
<xsl:template match="text:bookmark[starts-with(@text:name,'RANGE!')]"/>
<xsl:template match="text:bookmark[contains(@text:name, 'GoBack')]"/>
<xsl:template match="text:bookmark-start[contains(@text:name, 'GoBack')]"/>
<xsl:template match="text:bookmark-start[starts-with(@text:name, 'RANGE!')]"/>
<xsl:template match="text:bookmark-start[starts-with(@text:name, '__RefHeading___')]"/>
<xsl:template match="text:bookmark-start[starts-with(@text:name, '_Hlk')]"/>
<xsl:template match="text:bookmark-start[starts-with(@text:name, '_Toc')]"/>
<!--<xsl:template match="text:bookmark-start[starts-with(@text:name, '_Ref')]"/>-->
<xsl:template match="text:bookmark-end"/>
    
<!-- images en binaire -->
<xsl:template match="office:binary-data"/>
<!-- graphique word -->
<xsl:template match="draw:g"/>
<xsl:template match="draw:custom-shape"/>
    
</xsl:stylesheet>